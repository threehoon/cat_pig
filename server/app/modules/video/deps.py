import uuid
from typing import Annotated

from fastapi import Depends

from app.core.db import SessionDep
from app.core.exceptions import AppError, ErrorCode
from app.core.security import CurrentUserIdDep
from app.modules.points.deps import PointsServiceDep
from app.modules.video.repository import VideoRepository
from app.modules.video.service import VideoService


def parse_user_id(user_id: CurrentUserIdDep) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401) from exc


def get_video_repository(session: SessionDep) -> VideoRepository:
    return VideoRepository(session)


def get_video_service(
    repository: Annotated[VideoRepository, Depends(get_video_repository)],
    points: PointsServiceDep,
) -> VideoService:
    return VideoService(repository, points)


VideoUserIdDep = Annotated[uuid.UUID, Depends(parse_user_id)]
VideoServiceDep = Annotated[VideoService, Depends(get_video_service)]
