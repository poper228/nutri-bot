import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import analysis, common
from app.core.config import get_settings
from app.infrastructure.embeddings.encoder import get_embedder
from app.infrastructure.llm.factory import get_llm_provider
from app.infrastructure.vector_db.qdrant_client import QdrantStore, get_qdrant_client
from app.services.analysis.parser import AnalysisParser
from app.services.breakdown.builder import BreakdownBuilder
from app.services.lectures.retriever import LectureRetriever


def _build_breakdown_builder() -> BreakdownBuilder:
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
    return BreakdownBuilder(parser=parser, retriever=retriever, llm=llm)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()

    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")

    builder = _build_breakdown_builder()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Pass builder to handlers via workflow_data
    dp["builder"] = builder

    dp.include_router(common.router)
    dp.include_router(analysis.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
