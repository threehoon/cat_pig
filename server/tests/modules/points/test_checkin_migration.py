import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.db import engine
from app.modules.points.models import PointsCard, PointsCheckin


CHECKIN_COLUMNS = {"id", "user_id", "local_date", "source", "created_at"}
CARD_COLUMNS = {"user_id", "makeup_card_count"}


def load_revision() -> object:
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "0006_points_checkin.py"
    spec = importlib.util.spec_from_file_location("rev_0006_points_checkin", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_migration_matches_checkin_tables() -> None:
    revision = load_revision()
    assert revision.revision == "0006_points_checkin"
    assert revision.down_revision == "0005_points_entry"
    assert {column.name for column in PointsCheckin.__table__.columns} == CHECKIN_COLUMNS
    assert {column.name for column in PointsCard.__table__.columns} == CARD_COLUMNS

    def run_upgrade(connection: Connection) -> None:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            revision.upgrade()

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS migration_check CASCADE"))
        await conn.execute(text("CREATE SCHEMA migration_check"))
        await conn.execute(text("SET search_path TO migration_check, public"))
        await conn.run_sync(run_upgrade)
        checkin_columns = (
            await conn.execute(
                text(
                    """
                    SELECT column_name, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'migration_check'
                      AND table_name = 'points_checkin'
                    """
                )
            )
        ).all()
        card_columns = (
            await conn.execute(
                text(
                    """
                    SELECT column_name, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'migration_check'
                      AND table_name = 'points_card'
                    """
                )
            )
        ).all()
        unique_columns = (
            await conn.execute(
                text(
                    """
                    SELECT tc.table_name, kcu.column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                     AND tc.table_schema = kcu.table_schema
                     AND tc.table_name = kcu.table_name
                    WHERE tc.table_schema = 'migration_check'
                      AND tc.constraint_type = 'UNIQUE'
                      AND tc.table_name IN ('points_checkin', 'points_card')
                    ORDER BY tc.table_name, kcu.ordinal_position
                    """
                )
            )
        ).all()
        foreign_keys = (
            await conn.execute(
                text(
                    """
                    SELECT tc.table_name, kcu.column_name, rc.delete_rule
                    FROM information_schema.referential_constraints AS rc
                    JOIN information_schema.table_constraints AS tc
                      ON tc.constraint_name = rc.constraint_name
                     AND tc.constraint_schema = rc.constraint_schema
                    JOIN information_schema.key_column_usage AS kcu
                      ON kcu.constraint_name = tc.constraint_name
                     AND kcu.constraint_schema = tc.constraint_schema
                     AND kcu.table_name = tc.table_name
                    WHERE tc.table_schema = 'migration_check'
                      AND tc.table_name IN ('points_checkin', 'points_card')
                    """
                )
            )
        ).all()
        checks = (
            await conn.execute(
                text(
                    """
                    SELECT constraint_name, check_clause
                    FROM information_schema.check_constraints
                    WHERE constraint_schema = 'migration_check'
                      AND constraint_name IN (
                        'ck_points_checkin_source',
                        'ck_points_card_makeup_count'
                      )
                    """
                )
            )
        ).all()
        await conn.execute(text("DROP SCHEMA migration_check CASCADE"))
        await conn.execute(text("SET search_path TO public"))

    assert {row.column_name for row in checkin_columns} == CHECKIN_COLUMNS
    assert {row.column_name for row in card_columns} == CARD_COLUMNS
    assert all(row.is_nullable == "NO" for row in checkin_columns)
    assert all(row.is_nullable == "NO" for row in card_columns)
    checkin_defaults = {row.column_name: row.column_default for row in checkin_columns}
    card_defaults = {row.column_name: row.column_default for row in card_columns}
    assert checkin_defaults["created_at"] is not None
    assert "now" in checkin_defaults["created_at"]
    assert card_defaults["makeup_card_count"] is not None
    assert "0" in card_defaults["makeup_card_count"]
    assert [(row.table_name, row.column_name) for row in unique_columns] == [
        ("points_checkin", "user_id"),
        ("points_checkin", "local_date"),
    ]
    assert {(row.table_name, row.column_name, row.delete_rule) for row in foreign_keys} == {
        ("points_checkin", "user_id", "CASCADE"),
        ("points_card", "user_id", "CASCADE"),
    }
    clauses = {row.constraint_name: row.check_clause for row in checks}
    assert "checkin" in clauses["ck_points_checkin_source"]
    assert "makeup" in clauses["ck_points_checkin_source"]
    assert "makeup_card_count" in clauses["ck_points_card_makeup_count"]
    assert ">=" in clauses["ck_points_card_makeup_count"]
