import importlib.util
from pathlib import Path

from alembic.operations import Operations
from alembic.runtime.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Connection

from app.core.db import engine
from app.modules.community.models import (
    Comment,
    CommentLike,
    CommentReport,
    Follow,
    Post,
    PostFavorite,
    PostLike,
)


TABLES = {
    "post": Post,
    "post_like": PostLike,
    "post_favorite": PostFavorite,
    "comment": Comment,
    "comment_like": CommentLike,
    "comment_report": CommentReport,
    "follow": Follow,
}

EXPECTED_DELETE = {
    ("post", "user_id"): "CASCADE",
    ("post_like", "user_id"): "CASCADE",
    ("post_like", "post_id"): "CASCADE",
    ("post_favorite", "user_id"): "CASCADE",
    ("post_favorite", "post_id"): "CASCADE",
    ("comment", "post_id"): "CASCADE",
    ("comment", "user_id"): "CASCADE",
    ("comment", "parent_id"): "SET NULL",
    ("comment", "reply_to_user_id"): "CASCADE",
    ("comment_like", "user_id"): "CASCADE",
    ("comment_like", "comment_id"): "CASCADE",
    ("comment_report", "user_id"): "CASCADE",
    ("comment_report", "comment_id"): "CASCADE",
    ("follow", "follower_id"): "CASCADE",
    ("follow", "followee_id"): "CASCADE",
}

EXPECTED_INDEXES = {
    "ix_comment_post_created": ("post_id", "created_at"),
    "ix_post_status_created": ("status", "created_at"),
    "ix_post_user_created": ("user_id", "created_at"),
    "ix_follow_followee_created": ("followee_id", "created_at"),
}


def load_revision() -> object:
    path = Path(__file__).resolve().parents[3] / "alembic" / "versions" / "0008_community.py"
    spec = importlib.util.spec_from_file_location("rev_0008_community", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def test_migration_matches_community() -> None:
    revision = load_revision()
    assert revision.revision == "0008_community"
    assert revision.down_revision == "0007_media_object"

    def run_upgrade(connection: Connection) -> None:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            revision.upgrade()

    def run_downgrade(connection: Connection) -> None:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            revision.downgrade()

    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS migration_check CASCADE"))
        await conn.execute(text("CREATE SCHEMA migration_check"))
        await conn.execute(text("SET search_path TO migration_check, public"))
        try:
            await conn.run_sync(run_upgrade)
            columns = (
                await conn.execute(
                    text(
                        """
                        SELECT table_name, column_name, is_nullable, data_type
                        FROM information_schema.columns
                        WHERE table_schema = 'migration_check'
                          AND table_name IN (
                            'post', 'post_like', 'post_favorite', 'comment',
                            'comment_like', 'comment_report', 'follow'
                          )
                        """
                    )
                )
            ).all()
            foreign_keys = (
                await conn.execute(
                    text(
                        """
                        SELECT tc.table_name, kcu.column_name, rc.delete_rule
                        FROM information_schema.table_constraints AS tc
                        JOIN information_schema.key_column_usage AS kcu
                          ON tc.constraint_name = kcu.constraint_name
                         AND tc.constraint_schema = kcu.constraint_schema
                         AND tc.table_name = kcu.table_name
                        JOIN information_schema.referential_constraints AS rc
                          ON tc.constraint_name = rc.constraint_name
                         AND tc.constraint_schema = rc.constraint_schema
                        WHERE tc.table_schema = 'migration_check'
                          AND tc.constraint_type = 'FOREIGN KEY'
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
                        """
                    )
                )
            ).all()
            indexes = (
                await conn.execute(
                    text(
                        """
                        SELECT indexname, indexdef
                        FROM pg_indexes
                        WHERE schemaname = 'migration_check'
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
                         AND tc.constraint_schema = kcu.constraint_schema
                         AND tc.table_name = kcu.table_name
                        WHERE tc.table_schema = 'migration_check'
                          AND tc.constraint_type = 'UNIQUE'
                        """
                    )
                )
            ).all()
            await conn.run_sync(run_downgrade)
        finally:
            await conn.execute(text("DROP SCHEMA IF EXISTS migration_check CASCADE"))
            await conn.execute(text("SET search_path TO public"))

    by_table: dict[str, list] = {name: [] for name in TABLES}
    for row in columns:
        by_table[row.table_name].append(row)
    for name, model in TABLES.items():
        found = {row.column_name for row in by_table[name]}
        assert found == {column.name for column in model.__table__.columns}
        nulls = {row.column_name for row in by_table[name] if row.is_nullable == "YES"}
        model_nulls = {column.name for column in model.__table__.columns if column.nullable}
        assert nulls == model_nulls
        jsonb = {
            row.column_name
            for row in by_table[name]
            if row.data_type == "jsonb"
        }
        model_jsonb = {
            column.name
            for column in model.__table__.columns
            if isinstance(column.type, JSONB)
        }
        assert jsonb == model_jsonb

    rules: dict[tuple[str, str], str] = {}
    for row in foreign_keys:
        rules[(row.table_name, row.column_name)] = row.delete_rule
    assert rules == EXPECTED_DELETE

    clauses = {row.constraint_name: row.check_clause for row in checks}
    for word in ("draft", "pending", "published", "rejected"):
        assert word in clauses["ck_post_status"]
    for word in ("qa", "show", "share", "help", "daily", "experience"):
        assert word in clauses["ck_post_board"]
    assert "like_count" in clauses["ck_post_like_count"]
    assert "comment_count" in clauses["ck_post_comment_count"]
    assert "favorite_count" in clauses["ck_post_favorite_count"]
    assert "like_count" in clauses["ck_comment_like_count"]
    assert "audio_duration" in clauses["ck_comment_audio_duration"]
    assert "follower_id" in clauses["ck_follow_not_self"]
    assert "followee_id" in clauses["ck_follow_not_self"]

    indexdefs = {row.indexname: row.indexdef for row in indexes}
    for name, columns_ in EXPECTED_INDEXES.items():
        assert name in indexdefs
        for column in columns_:
            assert column in indexdefs[name]

    assert {row.column_name for row in unique_columns if row.table_name == "comment_report"} == {
        "user_id",
        "comment_id",
    }
