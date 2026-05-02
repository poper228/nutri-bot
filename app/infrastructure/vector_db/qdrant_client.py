from collections.abc import Iterable
from functools import lru_cache

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import (
    Distance,
    Filter,
    PointStruct,
    ScoredPoint,
    VectorParams,
)

from app.core.config import get_settings


@lru_cache(maxsize=1)
def get_qdrant_client() -> AsyncQdrantClient:
    settings = get_settings()
    return AsyncQdrantClient(
        host=settings.qdrant_host,
        port=settings.qdrant_http_port,
        prefer_grpc=False,
    )


class QdrantStore:
    def __init__(
        self,
        client: AsyncQdrantClient,
        collection_name: str,
        vector_size: int,
        distance: Distance = Distance.COSINE,
    ) -> None:
        self._client = client
        self._collection_name = collection_name
        self._vector_size = vector_size
        self._distance = distance

    @property
    def collection_name(self) -> str:
        return self._collection_name

    async def ensure_collection(self) -> None:
        if await self._client.collection_exists(self._collection_name):
            return
        await self._client.create_collection(
            collection_name=self._collection_name,
            vectors_config=VectorParams(size=self._vector_size, distance=self._distance),
        )

    async def upsert(self, points: Iterable[PointStruct]) -> None:
        await self._client.upsert(
            collection_name=self._collection_name,
            points=list(points),
            wait=True,
        )

    async def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        query_filter: Filter | None = None,
    ) -> list[ScoredPoint]:
        response = await self._client.query_points(
            collection_name=self._collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )
        return response.points

    async def delete_collection(self) -> None:
        await self._client.delete_collection(self._collection_name)
