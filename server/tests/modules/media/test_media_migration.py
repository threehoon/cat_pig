import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.db import engine
from app.modules.media.models import MediaObject


def load_revision() -> object:
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "0007_media_object.py"
    spec = importlib.util.spec_from_file_location("rev_0007_media_object", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_migration_matches_media_object() -> None:
    revision = load_revision()
    assert revision.revision == "0007_media_object"
    assert revision.down_revision == "0006_points_checkin"

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
                      AND table_name = 'media_object'
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
                      AND tc.table_name = 'media_object'
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
                      AND tc.table_name = 'media_object'
                    """
                )
            )
        ).scalar_one()
        await conn.execute(text("DROP SCHEMA migration_check CASCADE"))
        await conn.execute(text("SET search_path TO public"))

    assert {row.column_name for row in columns} == {column.name for column in MediaObject.__table__.columns}
    assert all(row.is_nullable == "NO" for row in columns)
    assert [row.column_name for row in unique_columns] == ["stored_name"]
    assert delete_rule == "CASCADE"
