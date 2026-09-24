import uuid
from typing import Annotated

from fastapi import Depends

from app.core.db import SessionDep
from app.core.exceptions import AppError, ErrorCode
from app.core.security import CurrentUserIdDep
from app.modules.media.repository import MediaRepository
from app.modules.media.service import MediaService


def parse_user_id(user_id: CurrentUserIdDep) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401) from exc


def get_media_repository(session: SessionDep) -> MediaRepository:
    return MediaRepository(session)


def get_media_service(
    repository: Annotated[MediaRepository, Depends(get_media_repository)],
) -> MediaService:
    return MediaService(repository)


MediaUserIdDep = Annotated[uuid.UUID, Depends(parse_user_id)]
MediaServiceDep = Annotated[MediaService, Depends(get_media_service)]
