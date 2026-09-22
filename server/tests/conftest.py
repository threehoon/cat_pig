import os
from collections.abc import AsyncIterator

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine.url import make_url


os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://app_pet:app_pet@127.0.0.1:5432/app_pet_test"
)

from app.core.db import Base, engine  # noqa: E402
from app.core.settings import get_settings  # noqa: E402
import app.modules.auth.models  # noqa: E402, F401
import app.modules.assistant.models  # noqa: E402, F401


get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    yield
    get_settings.cache_clear()


async def _ensure_vector_extension() -> None:
    """Install vector before the app engine connects.

    The engine registers the vector codec on connect, which fails if the
    extension is not already present. A raw connection avoids that hook.
    """
    url = make_url(get_settings().database_url)
    connection = await asyncpg.connect(
        user=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        database=url.database,
    )
    try:
        await connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
    finally:
        await connection.close()


@pytest_asyncio.fixture(autouse=True, loop_scope="function")
async def prepare_database() -> AsyncIterator[None]:
    get_settings.cache_clear()
    await _ensure_vector_extension()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE knowledge_chunk, knowledge_article, users CASCADE"
            )
        )
    await engine.dispose()
    get_settings.cache_clear()
