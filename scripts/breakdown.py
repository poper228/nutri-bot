import argparse
import asyncio
from pathlib import Path

from app.core.config import get_settings
from app.infrastructure.embeddings.encoder import get_embedder
from app.infrastructure.llm.factory import get_llm_provider
from app.infrastructure.vector_db.qdrant_client import QdrantStore, get_qdrant_client
from app.services.analysis.parser import AnalysisParser
from app.services.breakdown.builder import BreakdownBuilder
from app.services.lectures.retriever import LectureRetriever


async def run(path: Path) -> None:
    settings = get_settings()
    llm = get_llm_provider()
    embedder = get_embedder()
    store = QdrantStore(
        client=get_qdrant_client(),
        collection_name=settings.qdrant_lectures_collection,
        vector_size=settings.embedding_dimension,
    )
    retriever = LectureRetriever(embedder=embedder, vector_store=store)
    parser = AnalysisParser(llm=llm)
    builder = BreakdownBuilder(parser=parser, retriever=retriever, llm=llm)

    print(f"Анализирую {path.name}...\n")
    result = await builder.build(path)

    abnormal = [i for i in result.analysis.indicators if i.status in ("low", "high")]
    print(f"Показателей: {len(result.analysis.indicators)}, отклонений: {len(abnormal)}")
    print(f"RAG чанков использовано: {len(result.rag_chunks)}\n")
    print("=" * 60)
    print(result.text)
    print("=" * 60)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate nutritionist breakdown for lab analysis.")
    ap.add_argument("path", type=Path, help="Path to analysis PDF or image.")
    args = ap.parse_args()
    asyncio.run(run(args.path))


if __name__ == "__main__":
    main()
