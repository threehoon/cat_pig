import uuid
from typing import Annotated

from fastapi import Depends

from app.core.exceptions import AppError, ErrorCode
from app.core.security import CurrentUserIdDep
from app.modules.auth.deps import AuthServiceDep
from app.modules.community.deps import CommunityServiceDep
from app.modules.me.service import MeService
from app.modules.points.deps import PointsServiceDep


def parse_user_id(user_id: CurrentUserIdDep) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401) from exc


def get_me_service(
    auth: AuthServiceDep,
    points: PointsServiceDep,
    community: CommunityServiceDep,
) -> MeService:
    return MeService(auth, points, community)


MeUserIdDep = Annotated[uuid.UUID, Depends(parse_user_id)]
MeServiceDep = Annotated[MeService, Depends(get_me_service)]
