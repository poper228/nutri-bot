import argparse
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.infrastructure.embeddings.encoder import get_embedder
from app.infrastructure.vector_db.qdrant_client import QdrantStore, get_qdrant_client
from app.repositories.lecture_repository import LectureRepository
from app.services.lectures.indexer import LectureIndexer


async def index_one(pdf_path: Path) -> None:
    settings = get_settings()
    embedder = get_embedder()
    store = QdrantStore(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_lectures_collection,
        vector_size=settings.embedding_dimension,
    )

    factory = get_session_factory()
    async with factory() as session:
        repo = LectureRepository(session)
        indexer = LectureIndexer(repository=repo, vector_store=store, embedder=embedder)
        try:
            result = await indexer.index_pdf(pdf_path)
            await session.commit()
        except Exception:
            await session.rollback()
            raise

    print(
        f"OK: indexed lecture id={result.lecture_id}, "
        f"chunks={result.chunk_count}, file={pdf_path}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Index a lecture PDF into Postgres + Qdrant.")
    parser.add_argument("pdf_path", type=Path, help="Path to a PDF file with the lecture.")
    args = parser.parse_args()
    asyncio.run(index_one(args.pdf_path))


if __name__ == "__main__":
    main()
