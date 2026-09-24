from typing import Literal

from pydantic import BaseModel, ConfigDict


Visibility = Literal["public", "private", "friends"]


class Album(BaseModel):
    id: str
    title: str
    body: str
    image_urls: list[str]
    cover_url: str
    tag_names: list[str]
    visibility: Visibility
    sync_to_forum: bool
    created_at: str


class AlbumPage(BaseModel):
    items: list[Album]
    total: int
    page: int
    page_size: int


class AlbumWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = None
    body: str | None = None
    image_urls: list[str] | None = None
    cover_url: str | None = None
    tag_names: list[str] | None = None
    visibility: str | None = None
    sync_to_forum: bool | None = None


class AlbumDeleted(BaseModel):
    ok: bool
