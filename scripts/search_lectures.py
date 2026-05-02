import argparse
import asyncio

from app.core.config import get_settings
from app.infrastructure.embeddings.encoder import get_embedder
from app.infrastructure.vector_db.qdrant_client import QdrantStore, get_qdrant_client
from app.services.lectures.retriever import LectureRetriever


async def search(query: str, top_k: int) -> None:
    settings = get_settings()
    embedder = get_embedder()
    store = QdrantStore(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_lectures_collection,
        vector_size=settings.embedding_dimension,
    )
    retriever = LectureRetriever(embedder=embedder, vector_store=store)
    results = await retriever.search(query, top_k=top_k)

    if not results:
        print("No results.")
        return

    for i, r in enumerate(results, 1):
        preview = r.text[:200].replace("\n", " ")
        print(
            f"\n[{i}] score={r.score:.4f}  "
            f"lecture_id={r.lecture_id}  page={r.page_number}  chunk={r.chunk_index}"
        )
        print(f"     {preview}{'...' if len(r.text) > 200 else ''}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Search indexed lectures by query.")
    parser.add_argument("query", type=str, help="Free-form search query (Russian or English).")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    asyncio.run(search(args.query, args.top_k))


if __name__ == "__main__":
    main()
