from pathlib import Path

import pytest
import jwt
from httpx import AsyncClient, MockTransport, Request, Response
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.core.exceptions import AppError, ErrorCode
from app.core.pagination import PageQueryDep
from app.core.security import create_access_token, decode_access_token, require_user_id
from app.core.settings import get_settings
from app.core.wechat import exchange_code_for_openid
from app.main import create_app


def test_unknown_path_returns_not_found_envelope() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/no-such-route")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "NOT_FOUND", "message": "Resource not found"}
    }


def test_invalid_pagination_returns_validation_envelope() -> None:
    app = create_app()

    @app.get("/page")
    def read_page(query: PageQueryDep) -> dict[str, int]:
        return query.model_dump()

    with TestClient(app) as client:
        response = client.get("/page?page=0")

    assert response.status_code == 400
    assert response.json() == {
        "error": {"code": "VALIDATION", "message": "Request validation failed"}
    }


def test_pagination_has_defaults_and_no_maximum() -> None:
    app = create_app()

    @app.get("/page")
    def read_page(query: PageQueryDep) -> dict[str, int]:
        return query.model_dump()

    with TestClient(app) as client:
        default_response = client.get("/page")
        large_response = client.get("/page?page_size=1000")

    assert default_response.json() == {"page": 1, "page_size": 20}
    assert large_response.json() == {"page": 1, "page_size": 1000}


def test_app_error_keeps_stable_code_and_message() -> None:
    app = create_app()

    @app.get("/conflict")
    def conflict() -> None:
        raise AppError(ErrorCode.CONFLICT, "Already exists", 409)

    with TestClient(app) as client:
        response = client.get("/conflict")

    assert response.status_code == 409
    assert response.json() == {
        "error": {"code": "CONFLICT", "message": "Already exists"}
    }


def test_unexpected_error_is_not_exposed() -> None:
    app = create_app()

    @app.get("/crash")
    def crash() -> None:
        raise RuntimeError("database password leaked")

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/crash")

    assert response.status_code == 500
    assert response.json() == {
        "error": {"code": "INTERNAL", "message": "Internal server error"}
    }


def test_settings_load_server_env_independent_of_working_directory(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.database_url.endswith("/app_pet_test")
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_expire_seconds == 604800
    assert settings.wechat_appid == "wxe7c6ce42979250cd"
    assert settings.embedding_dim == 1024
    assert settings.embedding_min_cosine == 0.25


def test_local_without_wechat_secret_uses_fake_login(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("WECHAT_SECRET", "")
    get_settings.cache_clear()

    assert get_settings().is_local_fake_wechat() is True


def test_jwt_round_trip_keeps_string_user_id() -> None:
    token = create_access_token("user-123")
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    assert decode_access_token(token) == "user-123"
    assert require_user_id(credentials) == "user-123"


@pytest.mark.parametrize("credentials", [None, "not-a-jwt"])
def test_missing_or_invalid_bearer_is_unauthorized(
    credentials: str | None,
) -> None:
    bearer = (
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=credentials)
        if credentials
        else None
    )

    with pytest.raises(AppError) as error:
        require_user_id(bearer)

    assert error.value.code == ErrorCode.UNAUTHORIZED
    assert error.value.status_code == 401


def test_token_without_expiration_is_unauthorized() -> None:
    settings = get_settings()
    token = jwt.encode(
        {"sub": "user-123"},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(AppError) as error:
        decode_access_token(token)

    assert error.value.code == ErrorCode.UNAUTHORIZED


@pytest.mark.asyncio
async def test_blank_wechat_code_is_validation_error() -> None:
    with pytest.raises(AppError) as error:
        await exchange_code_for_openid("  ")

    assert error.value.code == ErrorCode.VALIDATION
    assert error.value.status_code == 400


@pytest.mark.asyncio
async def test_local_without_secret_returns_fake_openid(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "local")
    monkeypatch.setenv("WECHAT_SECRET", "")
    get_settings.cache_clear()

    assert await exchange_code_for_openid(" wx-code ") == "local:wx-code"


@pytest.mark.asyncio
async def test_prod_without_secret_rejects_login(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("WECHAT_SECRET", "")
    get_settings.cache_clear()

    with pytest.raises(AppError) as error:
        await exchange_code_for_openid("wx-code")

    assert error.value.code == ErrorCode.WECHAT_LOGIN_FAILED
    assert error.value.status_code == 502


@pytest.mark.asyncio
async def test_configured_wechat_login_returns_only_openid(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("WECHAT_SECRET", "test-secret")
    get_settings.cache_clear()

    def respond(request: Request) -> Response:
        assert request.url.params["appid"] == "wxe7c6ce42979250cd"
        assert request.url.params["secret"] == "test-secret"
        assert request.url.params["js_code"] == "wx-code"
        assert request.url.params["grant_type"] == "authorization_code"
        return Response(
            200,
            json={"openid": "wx-openid", "session_key": "must-not-escape"},
        )

    async with AsyncClient(transport=MockTransport(respond)) as client:
        openid = await exchange_code_for_openid("wx-code", client=client)

    assert openid == "wx-openid"


@pytest.mark.asyncio
async def test_wechat_api_error_uses_stable_login_error(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("WECHAT_SECRET", "test-secret")
    get_settings.cache_clear()

    transport = MockTransport(
        lambda _request: Response(200, json={"errcode": 40029, "errmsg": "invalid code"})
    )
    async with AsyncClient(transport=transport) as client:
        with pytest.raises(AppError) as error:
            await exchange_code_for_openid("wx-code", client=client)

    assert error.value.code == ErrorCode.WECHAT_LOGIN_FAILED
