import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.db import engine
from app.modules.auth.models import User


def load_revision() -> object:
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "0002_auth_users.py"
    spec = importlib.util.spec_from_file_location("rev_0002_auth_users", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_migration_matches_user_model() -> None:
    revision = load_revision()
    assert revision.revision == "0002_auth_users"
    assert revision.down_revision == "0001_vector_extension"

    def run_upgrade(connection: Connection) -> None:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            revision.upgrade()

    async with engine.begin() as conn:
        await conn.execute(text("CREATE SCHEMA migration_check"))
        await conn.execute(text("SET search_path TO migration_check"))
        await conn.run_sync(run_upgrade)
        columns = (
            await conn.execute(
                text(
                    """
                    SELECT column_name, is_nullable, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = 'migration_check' AND table_name = 'users'
                    """
                )
            )
        ).all()
        unique_columns = (
            await conn.execute(
                text(
                    """
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                     AND tc.table_name = kcu.table_name
                    WHERE tc.table_schema = 'migration_check'
                      AND tc.table_name = 'users'
                      AND tc.constraint_type = 'UNIQUE'
                    ORDER BY kcu.ordinal_position
                    """
                )
            )
        ).scalars().all()
        await conn.execute(text("DROP SCHEMA migration_check CASCADE"))
        await conn.execute(text("SET search_path TO public"))

    found = {row.column_name: row for row in columns}
    assert set(found) == {column.name for column in User.__table__.columns}
    assert found["openid"].character_maximum_length == 64
    assert found["openid"].is_nullable == "NO"
    assert found["nickname"].is_nullable == "YES"
    assert found["avatar_url"].is_nullable == "YES"
    assert found["id"].is_nullable == "NO"
    assert found["created_at"].is_nullable == "NO"
    assert list(unique_columns) == ["openid"]
