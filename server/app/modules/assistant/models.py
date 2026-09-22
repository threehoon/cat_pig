import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from pgvector.sqlalchemy import Vector as PgVector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Dialect,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    Uuid,
    text as sql_text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

EMBEDDING_DIM = 1024


class Vector(PgVector):
    """Bind a Python list so asyncpg's binary vector codec can encode it."""

    cache_ok = True

    def bind_processor(self, dialect: Dialect) -> Callable[[Any], list[float] | None]:
        def process(value: Any) -> list[float] | None:
            if value is None:
                return None
            if isinstance(value, list):
                return value
            return list(value)

        return process


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_article"
    __table_args__ = (
        CheckConstraint(
            "status IN ('published', 'archived')",
            name="ck_knowledge_article_status",
        ),
        UniqueConstraint("source_uri", name="uq_knowledge_article_source_uri"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    source_uri: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sql_text("now()"),
    )

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="article",
        cascade="all, delete-orphan",
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunk"
    __table_args__ = (
        UniqueConstraint(
            "article_id",
            "chunk_index",
            name="uq_knowledge_chunk_article_index",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("knowledge_article.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    embedding_model: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sql_text("now()"),
    )

    article: Mapped[KnowledgeArticle] = relationship(back_populates="chunks")


class Conversation(Base):
    __tablename__ = "conversation"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sql_text("now()"),
    )
