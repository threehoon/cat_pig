import uuid
from typing import Annotated

from fastapi import Depends

from app.core.db import SessionDep
from app.core.exceptions import AppError, ErrorCode
from app.core.security import CurrentUserIdDep
from app.modules.points.repository import PointsRepository
from app.modules.points.service import PointsService


def get_points_repository(session: SessionDep) -> PointsRepository:
    return PointsRepository(session)


def get_points_service(
    repository: Annotated[PointsRepository, Depends(get_points_repository)],
) -> PointsService:
    return PointsService(repository)


def parse_user_id(user_id: CurrentUserIdDep) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401) from exc


PointsServiceDep = Annotated[PointsService, Depends(get_points_service)]
PointsUserIdDep = Annotated[uuid.UUID, Depends(parse_user_id)]
