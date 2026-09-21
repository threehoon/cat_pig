import os

import pytest


os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://app_pet:app_pet@127.0.0.1:5432/app_pet_test"
)

from app.core.settings import get_settings  # noqa: E402


get_settings.cache_clear()


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    yield
    get_settings.cache_clear()
