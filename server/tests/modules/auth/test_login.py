import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient, Response
from sqlalchemy import select

from app.core.db import Base, SessionFactory
from app.core.security import decode_access_token
from app.core.settings import get_settings
from app.main import create_app
from app.modules.auth.models import User
from app.modules.auth.repository import UserRepository
from app.modules.auth.service import AuthService


async def fetch_users() -> list[User]:
    async with SessionFactory() as session:
        rows = await session.scalars(select(User))
        return list(rows.all())


async def post_login(client: AsyncClient, payload: dict[str, object]) -> Response:
    return await client.post("/api/v1/auth/login", json=payload)


def login_app() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=create_app()),
        base_url="http://test",
    )


async def test_login_returns_token_envelope() -> None:
    async with login_app() as client:
        response = await post_login(client, {"code": "test"})

    body = response.json()
    assert response.status_code == 200
    assert set(body) == {"data"}
    assert set(body["data"]) == {"token", "expires_in"}
    assert isinstance(body["data"]["token"], str)
    assert body["data"]["token"]
    assert body["data"]["expires_in"] == 604800
    assert "openid" not in response.text
    assert "session_key" not in response.text
    assert "points_balance" not in response.text


async def test_same_code_twice_reuses_one_user() -> None:
    async with login_app() as client:
        first = await post_login(client, {"code": "test"})
        second = await post_login(client, {"code": "test"})

    assert first.status_code == 200
    assert second.status_code == 200
    first_sub = decode_access_token(first.json()["data"]["token"])
    second_sub = decode_access_token(second.json()["data"]["token"])
    assert first_sub == second_sub
    uuid.UUID(first_sub)
    assert first_sub != "local:test"

    rows = await fetch_users()
    assert len(rows) == 1
    assert rows[0].nickname is None
    assert rows[0].avatar_url is None


async def test_trimmed_code_matches_untrimmed_code() -> None:
    async with login_app() as client:
        plain = await post_login(client, {"code": "test"})
        padded = await post_login(client, {"code": " test "})

    assert plain.status_code == 200
    assert padded.status_code == 200
    assert decode_access_token(plain.json()["data"]["token"]) == decode_access_token(
        padded.json()["data"]["token"]
    )


async def test_different_codes_create_different_users() -> None:
    async with login_app() as client:
        first = await post_login(client, {"code": "alpha"})
        second = await post_login(client, {"code": "beta"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert decode_access_token(first.json()["data"]["token"]) != decode_access_token(
        second.json()["data"]["token"]
    )
    assert len(await fetch_users()) == 2


@pytest.mark.parametrize("code", ["", "   "])
async def test_blank_code_is_validation(code: str) -> None:
    async with login_app() as client:
        response = await post_login(client, {"code": code})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION"


async def test_missing_code_is_validation() -> None:
    async with login_app() as client:
        response = await post_login(client, {})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION"


async def test_openid_at_column_limit_logs_in() -> None:
    async with login_app() as client:
        response = await post_login(client, {"code": "a" * 58})

    assert response.status_code == 200
    rows = await fetch_users()
    assert len(rows) == 1
    assert rows[0].openid == "local:" + ("a" * 58)
    assert len(rows[0].openid) == 64


async def test_openid_past_column_limit_is_validation() -> None:
    async with login_app() as client:
        response = await post_login(client, {"code": "a" * 59})

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION"
    assert await fetch_users() == []


async def test_prod_without_secret_is_wechat_login_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_ENV", "prod")
    monkeypatch.setenv("WECHAT_SECRET", "")
    get_settings.cache_clear()
    try:
        async with login_app() as client:
            response = await post_login(client, {"code": "test"})
        assert response.status_code == 502
        assert response.json()["error"]["code"] == "WECHAT_LOGIN_FAILED"
        assert await fetch_users() == []
    finally:
        monkeypatch.undo()
        get_settings.cache_clear()


async def test_concurrent_same_code_returns_one_user() -> None:
    async with login_app() as client:
        first, second = await asyncio.gather(
            post_login(client, {"code": "concurrent-code"}),
            post_login(client, {"code": "concurrent-code"}),
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert decode_access_token(first.json()["data"]["token"]) == decode_access_token(
        second.json()["data"]["token"]
    )
    assert len(await fetch_users()) == 1


async def test_service_login_upserts_one_user() -> None:
    async with SessionFactory() as session:
        service = AuthService(UserRepository(session))
        first = await service.login("svc-code")
        second = await service.login("svc-code")
        await session.commit()

    assert decode_access_token(first.token) == decode_access_token(second.token)
    rows = await fetch_users()
    assert len(rows) == 1


def test_metadata_registers_user_and_knowledge_tables() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "knowledge_article",
        "knowledge_chunk",
    }
    assert {column.name for column in User.__table__.columns} == {
        "id",
        "openid",
        "nickname",
        "avatar_url",
        "created_at",
    }
