import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from qdrant_client.http.models import PointStruct

from app.infrastructure.embeddings.encoder import E5Embedder
from app.infrastructure.vector_db.qdrant_client import QdrantStore
from app.repositories.lecture_repository import ChunkInput, LectureRepository
from app.services.lectures.chunker import chunk_pages
from app.services.lectures.pdf_parser import extract_pdf_pages


@dataclass(frozen=True, slots=True)
class IndexedLecture:
    lecture_id: int
    chunk_count: int


class LectureIndexer:
    def __init__(
        self,
        repository: LectureRepository,
        vector_store: QdrantStore,
        embedder: E5Embedder,
    ) -> None:
        self._repo = repository
        self._store = vector_store
        self._embedder = embedder

    async def index_pdf(self, file_path: Path | str) -> IndexedLecture:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"PDF not found: {path}")
        if not path.suffix.lower() == ".pdf":
            raise ValueError(f"Not a PDF file: {path}")

        existing = await self._repo.get_by_file_path(str(path))
        if existing is not None:
            raise ValueError(
                f"Lecture already indexed (id={existing.id}): {path}. "
                "Re-indexing is not supported yet."
            )

        pages = extract_pdf_pages(path)
        chunks = chunk_pages(pages)
        if not chunks:
            raise ValueError(f"No text extracted from {path}")

        texts = [c.text for c in chunks]
        vectors = await self._embedder.encode_documents(texts)

        point_ids = [uuid.uuid4() for _ in chunks]

        lecture = await self._repo.create(
            filename=path.name,
            file_path=str(path),
            title=path.stem,
        )
        chunk_inputs = [
            ChunkInput(
                chunk_index=c.chunk_index,
                page_number=c.page_number,
                text=c.text,
                qdrant_point_id=pid,
            )
            for c, pid in zip(chunks, point_ids, strict=True)
        ]
        await self._repo.add_chunks(lecture.id, chunk_inputs)

        await self._store.ensure_collection()
        points = [
            PointStruct(
                id=str(pid),
                vector=vec,
                payload={
                    "lecture_id": lecture.id,
                    "chunk_index": c.chunk_index,
                    "page_number": c.page_number,
                    "text": c.text,
                },
            )
            for c, pid, vec in zip(chunks, point_ids, vectors, strict=True)
        ]
        await self._store.upsert(points)

        await self._repo.mark_indexed(lecture.id, datetime.now(UTC))

        return IndexedLecture(lecture_id=lecture.id, chunk_count=len(chunks))
