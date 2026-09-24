"""Create points check-in days and makeup cards.

Revision ID: 0006_points_checkin
Revises: 0005_points_entry
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0006_points_checkin"
down_revision: str | Sequence[str] | None = "0005_points_entry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "points_checkin",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("source IN ('checkin', 'makeup')", name="ck_points_checkin_source"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_points_checkin_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "local_date", name="uq_points_checkin_user_date"),
    )
    op.create_table(
        "points_card",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "makeup_card_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.CheckConstraint("makeup_card_count >= 0", name="ck_points_card_makeup_count"),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_points_card_user_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("points_card")
    op.drop_table("points_checkin")
