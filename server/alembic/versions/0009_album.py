"""Create the album table.

Revision ID: 0009_album
Revises: 0008_community
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0009_album"
down_revision: str | Sequence[str] | None = "0008_community"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "album",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("image_urls", postgresql.JSONB(), nullable=False),
        sa.Column("cover_url", sa.Text(), nullable=False),
        sa.Column("tag_names", postgresql.JSONB(), nullable=False),
        sa.Column("visibility", sa.Text(), nullable=False),
        sa.Column("sync_to_forum", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "visibility IN ('public', 'private', 'friends')",
            name="ck_album_visibility",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_album_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_album_user_created",
        "album",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_album_user_created", table_name="album")
    op.drop_table("album")
