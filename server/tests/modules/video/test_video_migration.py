import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.db import engine
from app.modules.video.models import VideoTask


def load_revision() -> object:
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "0010_video_task.py"
    spec = importlib.util.spec_from_file_location("rev_0010_video_task", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_migration_matches_video_task() -> None:
    revision = load_revision()
    assert revision.revision == "0010_video_task"
    assert revision.down_revision == "0009_album"

    def run_upgrade(connection: Connection) -> None:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            revision.upgrade()

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS migration_check CASCADE"))
        await conn.execute(text("CREATE SCHEMA migration_check"))
        await conn.execute(text("SET search_path TO migration_check, public"))
        await conn.run_sync(run_upgrade)
        columns = (
            await conn.execute(
                text(
                    """
                    SELECT column_name, is_nullable, udt_name
                    FROM information_schema.columns
                    WHERE table_schema = 'migration_check'
                      AND table_name = 'video_task'
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
                      AND tc.table_name = 'video_task'
                    """
                )
            )
        ).scalar_one()
        referenced = (
            await conn.execute(
                text(
                    """
                    SELECT referenced.relname
                    FROM pg_constraint AS constraint_row
                    JOIN pg_class AS source ON source.oid = constraint_row.conrelid
                    JOIN pg_namespace AS namespace ON namespace.oid = source.relnamespace
                    JOIN pg_class AS referenced ON referenced.oid = constraint_row.confrelid
                    WHERE namespace.nspname = 'migration_check'
                      AND constraint_row.conname = 'fk_video_task_user_id'
                    """
                )
            )
        ).scalar_one()
        check_clause = (
            await conn.execute(
                text(
                    """
                    SELECT check_clause
                    FROM information_schema.check_constraints
                    WHERE constraint_schema = 'migration_check'
                      AND constraint_name = 'ck_video_task_status'
                    """
                )
            )
        ).scalar_one()
        indexdef = (
            await conn.execute(
                text(
                    """
                    SELECT indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'migration_check'
                      AND indexname = 'ix_video_task_user_created'
                    """
                )
            )
        ).scalar_one()
        await conn.execute(text("DROP SCHEMA migration_check CASCADE"))
        await conn.execute(text("SET search_path TO public"))

    by_name = {row.column_name: row for row in columns}
    assert set(by_name) == {column.name for column in VideoTask.__table__.columns}
    assert by_name["result_url"].is_nullable == "YES"
    assert by_name["error_message"].is_nullable == "YES"
    assert by_name["image_urls"].udt_name == "jsonb"
    for name, row in by_name.items():
        if name in {"result_url", "error_message"}:
            continue
        assert row.is_nullable == "NO"
    assert delete_rule == "CASCADE"
    assert referenced == "users"
    for status in ("pending", "running", "success", "failed"):
        assert status in check_clause
    assert "user_id" in indexdef
    assert "created_at" in indexdef
