import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import create_access_token, decode_access_token
from app.main import create_app


ME_FIELDS = {
    "id",
    "nickname",
    "avatar_url",
    "points_balance",
    "post_count",
    "like_received_count",
    "following_count",
    "follower_count",
}
NICKNAME_MESSAGE = "昵称须为 1–16 字"


def api() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, code: str = "me-user") -> str:
    response = await client.post("/api/v1/auth/login", json={"code": code})
    assert response.status_code == 200
    return response.json()["data"]["token"]


async def test_me_requires_a_token() -> None:
    async with api() as client:
        response = await client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_bad_token_is_unauthorized() -> None:
    async with api() as client:
        response = await client.get(
            "/api/v1/me",
            headers=bearer(create_access_token("not-a-uuid")),
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_missing_user_is_not_found() -> None:
    async with api() as client:
        response = await client.get(
            "/api/v1/me",
            headers=bearer(create_access_token(str(uuid.uuid4()))),
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_get_me_after_login() -> None:
    async with api() as client:
        token = await login(client)
        response = await client.get("/api/v1/me", headers=bearer(token))

    body = response.json()
    assert response.status_code == 200
    assert set(body) == {"data"}
    assert set(body["data"]) == ME_FIELDS
    assert body["data"]["id"] == decode_access_token(token)
    assert body["data"]["nickname"] is None
    assert body["data"]["avatar_url"] is None
    assert body["data"]["points_balance"] == 100
    assert body["data"]["post_count"] == 0
    assert body["data"]["like_received_count"] == 0
    assert body["data"]["following_count"] == 0
    assert body["data"]["follower_count"] == 0


async def test_patch_trims_nickname_and_keeps_balance() -> None:
    async with api() as client:
        token = await login(client)
        headers = bearer(token)
        saved = await client.patch(
            "/api/v1/me",
            headers=headers,
            json={"nickname": "  小满  ", "avatar_url": "https://example.com/a.jpg"},
        )
        again = await client.get("/api/v1/me", headers=headers)

    assert saved.status_code == 200
    assert saved.json()["data"]["nickname"] == "小满"
    assert saved.json()["data"]["avatar_url"] == "https://example.com/a.jpg"
    assert saved.json()["data"]["points_balance"] == 100
    assert again.json()["data"]["nickname"] == "小满"
    assert again.json()["data"]["avatar_url"] == "https://example.com/a.jpg"
    assert again.json()["data"]["points_balance"] == 100
    assert again.json()["data"]["post_count"] == 0


@pytest.mark.parametrize("nickname", ["", "   ", "a" * 17])
async def test_invalid_nickname_leaves_the_saved_name(nickname: str) -> None:
    async with api() as client:
        token = await login(client)
        headers = bearer(token)
        await client.patch(
            "/api/v1/me",
            headers=headers,
            json={"nickname": "小满", "avatar_url": "https://example.com/a.jpg"},
        )
        rejected = await client.patch(
            "/api/v1/me",
            headers=headers,
            json={"nickname": nickname, "avatar_url": "https://example.com/b.jpg"},
        )
        current = await client.get("/api/v1/me", headers=headers)

    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "VALIDATION"
    assert rejected.json()["error"]["message"] == NICKNAME_MESSAGE
    assert current.json()["data"]["nickname"] == "小满"
    assert current.json()["data"]["avatar_url"] == "https://example.com/a.jpg"
    assert current.json()["data"]["points_balance"] == 100


async def test_null_nickname_keeps_avatar() -> None:
    async with api() as client:
        token = await login(client)
        headers = bearer(token)
        await client.patch(
            "/api/v1/me",
            headers=headers,
            json={"nickname": "小满", "avatar_url": "https://example.com/a.jpg"},
        )
        cleared = await client.patch("/api/v1/me", headers=headers, json={"nickname": None})
        current = await client.get("/api/v1/me", headers=headers)

    assert cleared.status_code == 200
    assert current.json()["data"]["nickname"] is None
    assert current.json()["data"]["avatar_url"] == "https://example.com/a.jpg"
    assert current.json()["data"]["points_balance"] == 100


async def test_null_avatar_keeps_nickname() -> None:
    async with api() as client:
        token = await login(client)
        headers = bearer(token)
        await client.patch(
            "/api/v1/me",
            headers=headers,
            json={"nickname": "小满", "avatar_url": "https://example.com/a.jpg"},
        )
        cleared = await client.patch("/api/v1/me", headers=headers, json={"avatar_url": None})
        current = await client.get("/api/v1/me", headers=headers)

    assert cleared.status_code == 200
    assert current.json()["data"]["nickname"] == "小满"
    assert current.json()["data"]["avatar_url"] is None
    assert current.json()["data"]["points_balance"] == 100


async def test_published_post_shows_up_on_me() -> None:
    async with api() as client:
        token = await login(client, "me-counts")
        headers = bearer(token)
        created = await client.post(
            "/api/v1/community/post",
            headers=headers,
            json={
                "title": "出门",
                "body": "公园晒太阳",
                "image_urls": [],
                "topic_names": [],
                "status": "pending",
            },
        )
        me = await client.get("/api/v1/me", headers=headers)

    assert created.status_code == 200
    assert created.json()["data"]["status"] == "published"
    assert me.status_code == 200
    assert me.json()["data"]["post_count"] == 1
    assert me.json()["data"]["points_balance"] == 120
    assert me.json()["data"]["like_received_count"] == 0
    assert me.json()["data"]["following_count"] == 0
    assert me.json()["data"]["follower_count"] == 0


async def test_patch_rejects_balance_field() -> None:
    async with api() as client:
        token = await login(client)
        headers = bearer(token)
        await client.patch(
            "/api/v1/me",
            headers=headers,
            json={"nickname": "小满", "avatar_url": None},
        )
        rejected = await client.patch(
            "/api/v1/me",
            headers=headers,
            json={"nickname": "别的", "points_balance": 1},
        )
        current = await client.get("/api/v1/me", headers=headers)

    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "VALIDATION"
    assert current.json()["data"]["nickname"] == "小满"
    assert current.json()["data"]["points_balance"] == 100
