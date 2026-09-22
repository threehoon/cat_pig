import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


OPENID_MAX_LENGTH = 64


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("openid", name="uq_users_openid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    openid: Mapped[str] = mapped_column(String(OPENID_MAX_LENGTH), nullable=False)
    nickname: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
