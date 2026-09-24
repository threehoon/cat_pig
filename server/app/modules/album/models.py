import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Album(Base):
    __tablename__ = "album"
    __table_args__ = (
        CheckConstraint(
            "visibility IN ('public', 'private', 'friends')",
            name="ck_album_visibility",
        ),
        Index("ix_album_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_album_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    image_urls: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    cover_url: Mapped[str] = mapped_column(Text, nullable=False)
    tag_names: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    visibility: Mapped[str] = mapped_column(Text, nullable=False)
    sync_to_forum: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
