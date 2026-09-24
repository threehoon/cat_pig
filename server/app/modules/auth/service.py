import uuid

from app.core.exceptions import AppError, ErrorCode
from app.core.security import create_access_token
from app.core.settings import get_settings
from app.core.wechat import exchange_code_for_openid
from app.modules.auth.models import OPENID_MAX_LENGTH, User
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginResult, UserProfile
from app.modules.points.service import PointsService


class AuthService:
    def __init__(self, users: UserRepository, points: PointsService) -> None:
        self._users = users
        self._points = points

    async def login(self, code: str) -> LoginResult:
        openid = await exchange_code_for_openid(code)
        if len(openid) > OPENID_MAX_LENGTH:
            raise AppError(ErrorCode.VALIDATION, "WeChat code is too long", 400)
        user = await self._users.upsert_by_openid(openid)
        await self._points.grant_registration(user.id)
        settings = get_settings()
        return LoginResult(
            token=create_access_token(str(user.id)),
            expires_in=settings.jwt_expire_seconds,
        )

    async def get_profile(self, user_id: uuid.UUID) -> UserProfile:
        user = await self._require_user(user_id)
        return _profile(user)

    async def update_profile(
        self,
        user_id: uuid.UUID,
        changes: dict[str, str | None],
    ) -> UserProfile:
        user = await self._require_user(user_id)
        if changes:
            await self._users.apply_profile(user, changes)
        return _profile(user)

    async def _require_user(self, user_id: uuid.UUID) -> User:
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise AppError(ErrorCode.NOT_FOUND, "User not found", 404)
        return user


def _profile(user: User) -> UserProfile:
    return UserProfile(
        id=str(user.id),
        nickname=user.nickname,
        avatar_url=user.avatar_url,
    )
