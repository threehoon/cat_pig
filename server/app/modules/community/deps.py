import uuid
from typing import Annotated

from fastapi import Depends

from app.core.db import SessionDep
from app.core.exceptions import AppError, ErrorCode
from app.core.security import CurrentUserIdDep
from app.modules.auth.deps import AuthServiceDep
from app.modules.community.comment_repository import CommentRepository
from app.modules.community.follow_repository import FollowRepository
from app.modules.community.post_repository import PostRepository
from app.modules.community.service import CommunityService
from app.modules.points.deps import PointsServiceDep


def parse_user_id(user_id: CurrentUserIdDep) -> uuid.UUID:
    try:
        return uuid.UUID(user_id)
    except ValueError as exc:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401) from exc


def get_community_service(
    session: SessionDep,
    auth: AuthServiceDep,
    points: PointsServiceDep,
) -> CommunityService:
    return CommunityService(
        PostRepository(session),
        CommentRepository(session),
        FollowRepository(session),
        auth,
        points,
    )


CommunityUserIdDep = Annotated[uuid.UUID, Depends(parse_user_id)]
CommunityServiceDep = Annotated[CommunityService, Depends(get_community_service)]
