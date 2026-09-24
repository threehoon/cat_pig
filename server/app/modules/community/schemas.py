from typing import Literal

from pydantic import BaseModel, Field


Board = Literal["qa", "show", "share", "help", "daily", "experience"]
PostStatus = Literal["draft", "pending", "published", "rejected"]


class Author(BaseModel):
    id: str
    nickname: str | None
    avatar_url: str | None


class Post(BaseModel):
    id: str
    author: Author
    board: Board
    title: str
    body: str
    image_urls: list[str]
    topic_names: list[str]
    status: PostStatus
    followed: bool
    like_count: int
    comment_count: int
    favorite_count: int
    liked: bool
    favorited: bool
    created_at: str


class PostPage(BaseModel):
    items: list[Post]
    total: int
    page: int
    page_size: int


class PostCreate(BaseModel):
    board: str | None = None
    title: str = ""
    body: str = ""
    image_urls: list[str] = Field(default_factory=list)
    topic_names: list[str] = Field(default_factory=list)
    status: str = ""


class PostPatch(BaseModel):
    board: str | None = None
    title: str | None = None
    body: str | None = None
    image_urls: list[str] | None = None
    topic_names: list[str] | None = None
    status: str | None = None


class Comment(BaseModel):
    id: str
    author: Author
    body: str
    parent_id: str | None
    reply_to: Author | None
    sticker_ids: list[str]
    image_urls: list[str]
    audio_url: str | None
    audio_duration: int
    like_count: int
    liked: bool
    created_at: str


class CommentPage(BaseModel):
    items: list[Comment]
    total: int
    page: int
    page_size: int


class CommentCreate(BaseModel):
    body: str = ""
    parent_id: str | None = None
    sticker_ids: list[str] = Field(default_factory=list)
    image_urls: list[str] = Field(default_factory=list)
    audio_url: str | None = None
    audio_duration: int | None = 0


class CommentDeleteResult(BaseModel):
    ok: bool
    comment_count: int


class ReportCreate(BaseModel):
    reason: str = ""


class FollowCreate(BaseModel):
    user_id: str | None = None


class AuthorPage(BaseModel):
    items: list[Author]
    total: int
    page: int
    page_size: int


class OkResult(BaseModel):
    ok: bool


class ProfileCounts(BaseModel):
    post_count: int
    like_received_count: int
    following_count: int
    follower_count: int
