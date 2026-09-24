import os
import pkgutil
from collections.abc import AsyncIterator
from importlib import import_module, util

import asyncpg
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine.url import make_url

from app import modules


os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://app_pet:app_pet@127.0.0.1:5432/app_pet_test"
)

from app.core.db import Base, engine  # noqa: E402
from app.core.settings import get_settings  # noqa: E402


def _import_module_models() -> None:
    prefix = f"{modules.__name__}."
    for module_info in pkgutil.iter_modules(modules.__path__, prefix):
        if not module_info.ispkg:
            continue
        models_name = f"{module_info.name}.models"
        if util.find_spec(models_name) is not None:
            import_module(models_name)


_import_module_models()


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
        names = ", ".join(sorted(Base.metadata.tables))
        await conn.execute(text(f"TRUNCATE TABLE {names} CASCADE"))
    await engine.dispose()
    get_settings.cache_clear()
