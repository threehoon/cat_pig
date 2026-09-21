from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AppError, ErrorCode
from app.core.settings import get_settings


bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentialsDep = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]


def create_access_token(user_id: str) -> str:
    if not user_id:
        raise ValueError("user_id must not be empty")

    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(seconds=settings.jwt_expire_seconds)
    return jwt.encode(
        {"sub": user_id, "iat": issued_at, "exp": expires_at},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> str:
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
    except jwt.InvalidTokenError as exc:
        raise AppError(
            ErrorCode.UNAUTHORIZED,
            "Invalid or expired access token",
            401,
        ) from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        raise AppError(ErrorCode.UNAUTHORIZED, "Invalid access token", 401)
    return user_id


def require_user_id(credentials: BearerCredentialsDep) -> str:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(ErrorCode.UNAUTHORIZED, "Authentication required", 401)
    return decode_access_token(credentials.credentials)


CurrentUserIdDep = Annotated[str, Depends(require_user_id)]
