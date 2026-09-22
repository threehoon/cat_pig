from typing import Annotated

from fastapi import Depends

from app.core.db import SessionDep
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_auth_service(
    repository: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    return AuthService(repository)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
