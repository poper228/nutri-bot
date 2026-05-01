from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models import User


def test_settings_loads_required_fields() -> None:
    s = get_settings()
    assert s.postgres_user
    assert s.postgres_db
    assert s.llm_provider in ("gemini", "anthropic")
    assert s.database_url.startswith("postgresql+asyncpg://")
    assert s.qdrant_url.startswith("http://")


async def test_db_select_one(db_session: AsyncSession) -> None:
    result = await db_session.execute(text("SELECT 1"))
    assert result.scalar_one() == 1


async def test_users_table_is_queryable(db_session: AsyncSession) -> None:
    result = await db_session.execute(select(User))
    assert result.scalars().all() == []
