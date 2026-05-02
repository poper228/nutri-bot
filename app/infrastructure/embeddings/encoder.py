import asyncio
from functools import lru_cache
from typing import TYPE_CHECKING

from app.core.config import get_settings

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer

PASSAGE_PREFIX = "passage: "
QUERY_PREFIX = "query: "
DEFAULT_BATCH_SIZE = 32


class E5Embedder:
    def __init__(self, model_name: str, expected_dimension: int) -> None:
        self._model_name = model_name
        self._expected_dimension = expected_dimension
        self._model: SentenceTransformer | None = None

    @property
    def dimension(self) -> int:
        return self._expected_dimension

    def _load_model(self) -> "SentenceTransformer":
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer

        model = SentenceTransformer(self._model_name)
        actual = model.get_sentence_embedding_dimension()
        if actual != self._expected_dimension:
            raise RuntimeError(
                f"Embedding dimension mismatch: model {self._model_name!r} "
                f"produces vectors of size {actual}, but config expects "
                f"{self._expected_dimension}."
            )
        self._model = model
        return model

    def _encode_sync(
        self,
        texts: list[str],
        batch_size: int,
    ) -> list[list[float]]:
        model = self._load_model()
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return embeddings.tolist()

    async def encode_documents(
        self,
        texts: list[str],
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> list[list[float]]:
        prefixed = [PASSAGE_PREFIX + t for t in texts]
        return await asyncio.to_thread(self._encode_sync, prefixed, batch_size)

    async def encode_query(self, text: str) -> list[float]:
        prefixed = [QUERY_PREFIX + text]
        result = await asyncio.to_thread(self._encode_sync, prefixed, 1)
        return result[0]


@lru_cache(maxsize=1)
def get_embedder() -> E5Embedder:
    settings = get_settings()
    return E5Embedder(
        model_name=settings.embedding_model,
        expected_dimension=settings.embedding_dimension,
    )
