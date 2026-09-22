from app.core.exceptions import AppError, ErrorCode
from app.core.security import create_access_token
from app.core.settings import get_settings
from app.core.wechat import exchange_code_for_openid
from app.modules.auth.models import OPENID_MAX_LENGTH
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginResult


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def login(self, code: str) -> LoginResult:
        openid = await exchange_code_for_openid(code)
        if len(openid) > OPENID_MAX_LENGTH:
            raise AppError(ErrorCode.VALIDATION, "WeChat code is too long", 400)
        user = await self._users.upsert_by_openid(openid)
        settings = get_settings()
        return LoginResult(
            token=create_access_token(str(user.id)),
            expires_in=settings.jwt_expire_seconds,
        )
