from typing import Annotated

from fastapi import APIRouter, Query

from app.core.envelope import DataEnvelope
from app.core.pagination import PageQueryDep
from app.modules.video.deps import VideoServiceDep, VideoUserIdDep
from app.modules.video.schemas import DeleteResult, Video, VideoCreate, VideoPage


router = APIRouter()


@router.get("")
async def list_videos(
    user_id: VideoUserIdDep,
    service: VideoServiceDep,
    page: PageQueryDep,
    status: Annotated[str | None, Query()] = None,
) -> DataEnvelope[VideoPage]:
    return DataEnvelope(data=await service.list_videos(user_id, page, status))


@router.post("")
async def create_video(
    body: VideoCreate,
    user_id: VideoUserIdDep,
    service: VideoServiceDep,
) -> DataEnvelope[Video]:
    return DataEnvelope(data=await service.create_video(user_id, body))


@router.get("/{video_id}")
async def get_video(
    video_id: str,
    user_id: VideoUserIdDep,
    service: VideoServiceDep,
) -> DataEnvelope[Video]:
    return DataEnvelope(data=await service.get_video(user_id, video_id))


@router.delete("/{video_id}")
async def delete_video(
    video_id: str,
    user_id: VideoUserIdDep,
    service: VideoServiceDep,
) -> DataEnvelope[DeleteResult]:
    return DataEnvelope(data=await service.delete_video(user_id, video_id))
