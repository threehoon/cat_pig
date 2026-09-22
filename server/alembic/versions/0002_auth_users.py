"""Create the users table.

Revision ID: 0002_auth_users
Revises: 0001_vector_extension
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_auth_users"
down_revision: str | Sequence[str] | None = "0001_vector_extension"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("openid", sa.String(length=64), nullable=False),
        sa.Column("nickname", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("openid", name="uq_users_openid"),
    )


def downgrade() -> None:
    op.drop_table("users")
