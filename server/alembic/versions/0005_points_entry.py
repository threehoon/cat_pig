"""Create the points ledger.

Revision ID: 0005_points_entry
Revises: 0004_assistant_conversation
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0005_points_entry"
down_revision: str | Sequence[str] | None = "0004_assistant_conversation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "points_entry",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("balance_after", sa.Integer(), nullable=False),
        sa.Column("event_key", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("kind IN ('earn', 'spend')", name="ck_points_entry_kind"),
        sa.CheckConstraint("amount > 0", name="ck_points_entry_amount"),
        sa.CheckConstraint("balance_after >= 0", name="ck_points_entry_balance_after"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_points_entry_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_key", name="uq_points_entry_event_key"),
    )
    op.create_index(
        "ix_points_entry_user_created",
        "points_entry",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_points_entry_user_created", table_name="points_entry")
    op.drop_table("points_entry")
