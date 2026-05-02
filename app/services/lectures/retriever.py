from dataclasses import dataclass

from app.infrastructure.embeddings.encoder import E5Embedder
from app.infrastructure.vector_db.qdrant_client import QdrantStore


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    score: float
    lecture_id: int
    chunk_index: int
    page_number: int
    text: str


class LectureRetriever:
    def __init__(self, embedder: E5Embedder, vector_store: QdrantStore) -> None:
        self._embedder = embedder
        self._store = vector_store

    async def search(self, query: str, top_k: int = 5) -> list[RetrievalResult]:
        if not query.strip():
            return []

        query_vector = await self._embedder.encode_query(query)
        scored = await self._store.search(query_vector=query_vector, top_k=top_k)

        results: list[RetrievalResult] = []
        for point in scored:
            payload = point.payload or {}
            results.append(
                RetrievalResult(
                    score=point.score,
                    lecture_id=int(payload.get("lecture_id", 0)),
                    chunk_index=int(payload.get("chunk_index", 0)),
                    page_number=int(payload.get("page_number", 0)),
                    text=str(payload.get("text", "")),
                )
            )
        return results
