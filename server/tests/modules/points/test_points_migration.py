import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.db import engine
from app.modules.points.models import PointsEntry


def load_revision() -> object:
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "0005_points_entry.py"
    spec = importlib.util.spec_from_file_location("rev_0005_points_entry", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_migration_matches_points_entry() -> None:
    revision = load_revision()
    assert revision.revision == "0005_points_entry"
    assert revision.down_revision == "0004_assistant_conversation"

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
                    SELECT column_name, is_nullable
                    FROM information_schema.columns
                    WHERE table_schema = 'migration_check'
                      AND table_name = 'points_entry'
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
                      AND tc.table_name = 'points_entry'
                      AND tc.constraint_type = 'UNIQUE'
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
                      AND tc.table_name = 'points_entry'
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
                      AND constraint_name IN (
                        'ck_points_entry_kind',
                        'ck_points_entry_amount',
                        'ck_points_entry_balance_after'
                      )
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
                      AND indexname = 'ix_points_entry_user_created'
                    """
                )
            )
        ).scalar_one()
        await conn.execute(text("DROP SCHEMA migration_check CASCADE"))
        await conn.execute(text("SET search_path TO public"))

    assert {row.column_name for row in columns} == {column.name for column in PointsEntry.__table__.columns}
    assert all(row.is_nullable == "NO" for row in columns)
    assert [row.column_name for row in unique_columns] == ["event_key"]
    assert delete_rule == "CASCADE"
    clauses = {row.constraint_name: row.check_clause for row in checks}
    assert "earn" in clauses["ck_points_entry_kind"]
    assert "spend" in clauses["ck_points_entry_kind"]
    assert "amount" in clauses["ck_points_entry_amount"]
    assert "balance_after" in clauses["ck_points_entry_balance_after"]
    assert "user_id" in indexdef
    assert "created_at" in indexdef
