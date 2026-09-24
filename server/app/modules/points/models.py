import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PointsEntry(Base):
    __tablename__ = "points_entry"
    __table_args__ = (
        CheckConstraint("kind IN ('earn', 'spend')", name="ck_points_entry_kind"),
        CheckConstraint("amount > 0", name="ck_points_entry_amount"),
        CheckConstraint("balance_after >= 0", name="ck_points_entry_balance_after"),
        UniqueConstraint("event_key", name="uq_points_entry_event_key"),
        Index("ix_points_entry_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_points_entry_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    event_key: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


class PointsCheckin(Base):
    __tablename__ = "points_checkin"
    __table_args__ = (
        CheckConstraint("source IN ('checkin', 'makeup')", name="ck_points_checkin_source"),
        UniqueConstraint("user_id", "local_date", name="uq_points_checkin_user_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_points_checkin_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    local_date: Mapped[date] = mapped_column(Date, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )


class PointsCard(Base):
    __tablename__ = "points_card"
    __table_args__ = (
        CheckConstraint("makeup_card_count >= 0", name="ck_points_card_makeup_count"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_points_card_user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    makeup_card_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
    )
