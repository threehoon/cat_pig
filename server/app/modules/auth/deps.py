from typing import Annotated

from fastapi import Depends

from app.core.db import SessionDep
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService
from app.modules.points.deps import PointsServiceDep


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
    points: PointsServiceDep,
) -> AuthService:
    return AuthService(repository, points)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
