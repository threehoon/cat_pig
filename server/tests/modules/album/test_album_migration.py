import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.db import engine
from app.modules.album.models import Album


def load_revision() -> object:
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "0009_album.py"
    spec = importlib.util.spec_from_file_location("rev_0009_album", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_migration_matches_album() -> None:
    revision = load_revision()
    assert revision.revision == "0009_album"
    assert revision.down_revision == "0008_community"

    def run_upgrade(connection: Connection) -> None:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            revision.upgrade()

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS migration_check CASCADE"))
        await conn.execute(text("CREATE SCHEMA migration_check"))
        # SET LOCAL ends with this transaction, so a failure cannot leak search_path.
        await conn.execute(text("SET LOCAL search_path TO migration_check, public"))
        await conn.run_sync(run_upgrade)
        columns = (
            await conn.execute(
                text(
                    """
                    SELECT column_name, is_nullable, udt_name
                    FROM information_schema.columns
                    WHERE table_schema = 'migration_check'
                      AND table_name = 'album'
                    """
                )
            )
        ).all()
        delete_rule = (
            await conn.execute(
                text(
                    """
                    SELECT rc.delete_rule
                    FROM information_schema.referential_constraints AS rc
                    JOIN information_schema.table_constraints AS tc
                      ON tc.constraint_name = rc.constraint_name
                     AND tc.constraint_schema = rc.constraint_schema
                    WHERE tc.table_schema = 'migration_check'
                      AND tc.table_name = 'album'
                    """
                )
            )
        ).scalar_one()
        checks = (
            await conn.execute(
                text(
                    """
                    SELECT constraint_name, check_clause
                    FROM information_schema.check_constraints
                    WHERE constraint_schema = 'migration_check'
                      AND constraint_name = 'ck_album_visibility'
                    """
                )
            )
        ).all()
        indexdef = (
            await conn.execute(
                text(
                    """
                    SELECT indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'migration_check'
                      AND indexname = 'ix_album_user_created'
                    """
                )
            )
        ).scalar_one()
        await conn.execute(text("DROP SCHEMA IF EXISTS migration_check CASCADE"))

    found = {row.column_name: row for row in columns}
    assert set(found) == {column.name for column in Album.__table__.columns}
    assert all(row.is_nullable == "NO" for row in columns)
    assert found["id"].udt_name == "uuid"
    assert found["user_id"].udt_name == "uuid"
    assert found["image_urls"].udt_name == "jsonb"
    assert found["tag_names"].udt_name == "jsonb"
    assert found["sync_to_forum"].udt_name == "bool"
    assert found["created_at"].udt_name == "timestamptz"
    assert delete_rule == "CASCADE"
    clauses = {row.constraint_name: row.check_clause for row in checks}
    clause = clauses["ck_album_visibility"]
    assert "public" in clause
    assert "private" in clause
    assert "friends" in clause
    assert "user_id" in indexdef
    assert "created_at" in indexdef
