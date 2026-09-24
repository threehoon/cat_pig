"""Create community posts, comments, and follows.

Revision ID: 0008_community
Revises: 0007_media_object
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0008_community"
down_revision: str | Sequence[str] | None = "0007_media_object"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "post",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("board", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column("body", sa.Text(), server_default=sa.text("''"), nullable=False),
        sa.Column(
            "image_urls",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "topic_names",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("like_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("comment_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("favorite_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "board IN ('qa', 'show', 'share', 'help', 'daily', 'experience')",
            name="ck_post_board",
        ),
        sa.CheckConstraint(
            "status IN ('draft', 'pending', 'published', 'rejected')",
            name="ck_post_status",
        ),
        sa.CheckConstraint("like_count >= 0", name="ck_post_like_count"),
        sa.CheckConstraint("comment_count >= 0", name="ck_post_comment_count"),
        sa.CheckConstraint("favorite_count >= 0", name="ck_post_favorite_count"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_post_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_post_status_created", "post", ["status", "created_at"])
    op.create_index("ix_post_user_created", "post", ["user_id", "created_at"])
    op.create_table(
        "post_like",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_post_like_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["post.id"],
            name="fk_post_like_post_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "post_id"),
    )
    op.create_table(
        "post_favorite",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_post_favorite_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["post.id"],
            name="fk_post_favorite_post_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "post_id"),
    )
    op.create_table(
        "comment",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Uuid(), nullable=True),
        sa.Column("reply_to_user_id", sa.Uuid(), nullable=True),
        sa.Column(
            "sticker_ids",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "image_urls",
            postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("audio_duration", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("like_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("like_count >= 0", name="ck_comment_like_count"),
        sa.CheckConstraint("audio_duration >= 0", name="ck_comment_audio_duration"),
        sa.ForeignKeyConstraint(
            ["post_id"],
            ["post.id"],
            name="fk_comment_post_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_comment_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["comment.id"],
            name="fk_comment_parent_id",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["reply_to_user_id"],
            ["users.id"],
            name="fk_comment_reply_to_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_comment_post_created", "comment", ["post_id", "created_at"])
    op.create_table(
        "comment_like",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("comment_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_comment_like_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["comment_id"],
            ["comment.id"],
            name="fk_comment_like_comment_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "comment_id"),
    )
    op.create_table(
        "comment_report",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("comment_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["comment_id"],
            ["comment.id"],
            name="fk_comment_report_comment_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_comment_report_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "comment_id", name="uq_comment_report_user_comment"),
    )
    op.create_table(
        "follow",
        sa.Column("follower_id", sa.Uuid(), nullable=False),
        sa.Column("followee_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("follower_id <> followee_id", name="ck_follow_not_self"),
        sa.ForeignKeyConstraint(
            ["follower_id"],
            ["users.id"],
            name="fk_follow_follower_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["followee_id"],
            ["users.id"],
            name="fk_follow_followee_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("follower_id", "followee_id"),
    )
    op.create_index("ix_follow_followee_created", "follow", ["followee_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_follow_followee_created", table_name="follow")
    op.drop_table("follow")
    op.drop_table("comment_report")
    op.drop_table("comment_like")
    op.drop_index("ix_comment_post_created", table_name="comment")
    op.drop_table("comment")
    op.drop_table("post_favorite")
    op.drop_table("post_like")
    op.drop_index("ix_post_user_created", table_name="post")
    op.drop_index("ix_post_status_created", table_name="post")
    op.drop_table("post")
