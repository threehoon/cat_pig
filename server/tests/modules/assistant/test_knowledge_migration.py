import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.core.db import engine
from app.modules.assistant.models import KnowledgeArticle, KnowledgeChunk


def load_revision() -> object:
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "0003_assistant_knowledge.py"
    spec = importlib.util.spec_from_file_location("rev_0003_assistant_knowledge", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_migration_matches_knowledge_models() -> None:
    revision = load_revision()
    assert revision.revision == "0003_assistant_knowledge"
    assert revision.down_revision == "0002_auth_users"

    def run_upgrade(connection: Connection) -> None:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            revision.upgrade()

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS migration_check CASCADE"))
        await conn.execute(text("CREATE SCHEMA migration_check"))
        # vector is installed in public. Keep migration_check first so unqualified
        # tables and the HNSW index land there, not in public.
        await conn.execute(text("SET search_path TO migration_check, public"))
        await conn.run_sync(run_upgrade)
        columns = (
            await conn.execute(
                text(
                    """
                    SELECT table_name, column_name, is_nullable, udt_name
                    FROM information_schema.columns
                    WHERE table_schema = 'migration_check'
                      AND table_name IN ('knowledge_article', 'knowledge_chunk')
                    """
                )
            )
        ).all()
        embedding_type = (
            await conn.execute(
                text(
                    """
                    SELECT format_type(attribute.atttypid, attribute.atttypmod)
                    FROM pg_attribute AS attribute
                    JOIN pg_class AS relation ON relation.oid = attribute.attrelid
                    JOIN pg_namespace AS namespace ON namespace.oid = relation.relnamespace
                    WHERE namespace.nspname = 'migration_check'
                      AND relation.relname = 'knowledge_chunk'
                      AND attribute.attname = 'embedding'
                    """
                )
            )
        ).scalar_one()
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
                    ORDER BY tc.table_name, kcu.ordinal_position
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
                      AND tc.table_name = 'knowledge_chunk'
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
                      AND constraint_name = 'ck_knowledge_article_status'
                    """
                )
            )
        ).scalar_one()
        hnsw = (
            await conn.execute(
                text(
                    """
                    SELECT indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'migration_check'
                      AND indexname = 'ix_knowledge_chunk_embedding'
                    """
                )
            )
        ).all()
        public_hnsw = (
            await conn.execute(
                text(
                    """
                    SELECT indexdef
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND indexname = 'ix_knowledge_chunk_embedding'
                    """
                )
            )
        ).all()
        await conn.execute(text("DROP SCHEMA migration_check CASCADE"))
        await conn.execute(text("SET search_path TO public"))

    article_columns = {row.column_name: row for row in columns if row.table_name == "knowledge_article"}
    chunk_columns = {row.column_name: row for row in columns if row.table_name == "knowledge_chunk"}
    assert set(article_columns) == {column.name for column in KnowledgeArticle.__table__.columns}
    assert set(chunk_columns) == {column.name for column in KnowledgeChunk.__table__.columns}
    assert all(row.is_nullable == "NO" for row in columns)
    assert chunk_columns["embedding"].udt_name == "vector"
    assert embedding_type == "vector(1024)"
    assert sorted(unique_columns) == [
        ("knowledge_article", "source_uri"),
        ("knowledge_chunk", "article_id"),
        ("knowledge_chunk", "chunk_index"),
    ]
    assert delete_rule == "CASCADE"
    assert "published" in check_clause
    assert "archived" in check_clause
    assert len(hnsw) == 1
    assert "vector_cosine_ops" in hnsw[0].indexdef
    assert public_hnsw == []
