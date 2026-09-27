import pytest

from tests.conftest import require_test_database


_PREFIX = "postgresql+asyncpg://app_pet:app_pet@127.0.0.1:5432/"


def test_app_pet_test_is_accepted() -> None:
    require_test_database(f"{_PREFIX}app_pet_test")


def test_app_pet_is_rejected() -> None:
    with pytest.raises(RuntimeError):
        require_test_database(f"{_PREFIX}app_pet")


def test_app_pet_test_backup_is_rejected() -> None:
    with pytest.raises(RuntimeError):
        require_test_database(f"{_PREFIX}app_pet_test_backup")
