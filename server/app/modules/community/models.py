import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import now_utc
from app.core.db import Base


def _empty_list() -> list[str]:
    return []


class Post(Base):
    __tablename__ = "post"
    __table_args__ = (
        CheckConstraint(
            "board IN ('qa', 'show', 'share', 'help', 'daily', 'experience')",
            name="ck_post_board",
        ),
        CheckConstraint(
            "status IN ('draft', 'pending', 'published', 'rejected')",
            name="ck_post_status",
        ),
        CheckConstraint("like_count >= 0", name="ck_post_like_count"),
        CheckConstraint("comment_count >= 0", name="ck_post_comment_count"),
        CheckConstraint("favorite_count >= 0", name="ck_post_favorite_count"),
        Index("ix_post_status_created", "status", "created_at"),
        Index("ix_post_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_post_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    board: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default=text("''"))
    body: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default=text("''"))
    image_urls: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=_empty_list,
        server_default=text("'[]'::jsonb"),
    )
    topic_names: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=_empty_list,
        server_default=text("'[]'::jsonb"),
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    comment_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    favorite_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
        server_default=text("now()"),
    )


class PostLike(Base):
    __tablename__ = "post_like"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_post_like_user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("post.id", name="fk_post_like_post_id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
        server_default=text("now()"),
    )


class PostFavorite(Base):
    __tablename__ = "post_favorite"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_post_favorite_user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("post.id", name="fk_post_favorite_post_id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
        server_default=text("now()"),
    )


class Comment(Base):
    __tablename__ = "comment"
    __table_args__ = (
        CheckConstraint("like_count >= 0", name="ck_comment_like_count"),
        CheckConstraint("audio_duration >= 0", name="ck_comment_audio_duration"),
        Index("ix_comment_post_created", "post_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("post.id", name="fk_comment_post_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_comment_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("comment.id", name="fk_comment_parent_id", ondelete="SET NULL"),
        nullable=True,
    )
    reply_to_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_comment_reply_to_user_id", ondelete="CASCADE"),
        nullable=True,
    )
    sticker_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=_empty_list,
        server_default=text("'[]'::jsonb"),
    )
    image_urls: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=_empty_list,
        server_default=text("'[]'::jsonb"),
    )
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    like_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
        server_default=text("now()"),
    )


class CommentLike(Base):
    __tablename__ = "comment_like"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_comment_like_user_id", ondelete="CASCADE"),
        primary_key=True,
    )
    comment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("comment.id", name="fk_comment_like_comment_id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
        server_default=text("now()"),
    )


class CommentReport(Base):
    __tablename__ = "comment_report"
    __table_args__ = (
        UniqueConstraint("user_id", "comment_id", name="uq_comment_report_user_comment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    comment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("comment.id", name="fk_comment_report_comment_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_comment_report_user_id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
        server_default=text("now()"),
    )


class Follow(Base):
    __tablename__ = "follow"
    __table_args__ = (
        CheckConstraint("follower_id <> followee_id", name="ck_follow_not_self"),
        Index("ix_follow_followee_created", "followee_id", "created_at"),
    )

    follower_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_follow_follower_id", ondelete="CASCADE"),
        primary_key=True,
    )
    followee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", name="fk_follow_followee_id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=now_utc,
        server_default=text("now()"),
    )
