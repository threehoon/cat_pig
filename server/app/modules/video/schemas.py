from typing import Literal

from pydantic import BaseModel


VideoResolution = Literal["540p", "720p", "1080p", "2k", "4k"]
VideoStatus = Literal["pending", "running", "success", "failed"]


class VideoCreate(BaseModel):
    title: str | None = None
    image_urls: list[str]
    prompt: str | None = None
    resolution: str


class Video(BaseModel):
    id: str
    title: str
    image_urls: list[str]
    prompt: str
    resolution: VideoResolution
    status: VideoStatus
    result_url: str | None
    points_cost: int
    error_message: str | None
    created_at: str


class VideoPage(BaseModel):
    items: list[Video]
    total: int
    page: int
    page_size: int


class DeleteResult(BaseModel):
    ok: bool
