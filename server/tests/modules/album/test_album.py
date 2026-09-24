import re
import uuid

import pytest
from httpx import ASGITransport, AsyncClient, Response

from app.core.security import decode_access_token
from app.main import create_app


ALBUM_FIELDS = {
    "id",
    "title",
    "body",
    "image_urls",
    "cover_url",
    "tag_names",
    "visibility",
    "sync_to_forum",
    "created_at",
}
PAGE_FIELDS = {"items", "total", "page", "page_size"}
CREATED_AT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
PHOTO_COUNT = "照片数量须为 1\u20139 张"


def api() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def write_album(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "title": "周末出门",
        "body": "去公园晒太阳",
        "image_urls": ["https://example.com/1.jpg"],
        "tag_names": ["生活"],
        "sync_to_forum": False,
    }
    payload.update(overrides)
    return payload


def urls(count: int) -> list[str]:
    return [f"https://example.com/{index}.jpg" for index in range(count)]


async def login(client: AsyncClient, code: str | None = None) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={"code": code or f"album-{uuid.uuid4()}"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["token"]
    assert isinstance(token, str) and token
    return token


def assert_error(response: Response, status: int, code: str, message: str) -> None:
    body = response.json()
    assert response.status_code == status
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["message"] == message


def assert_album(data: dict[str, object], **expected: object) -> None:
    assert set(data) == ALBUM_FIELDS
    assert isinstance(data["id"], str)
    uuid.UUID(data["id"])
    assert isinstance(data["created_at"], str)
    assert CREATED_AT.fullmatch(data["created_at"])
    assert isinstance(data["tag_names"], list)
    assert isinstance(data["image_urls"], list)
    assert isinstance(data["sync_to_forum"], bool)
    for key, value in expected.items():
        assert data[key] == value


def publish_album_show_ready() -> bool:
    try:
        import app.modules.community.service as community_service
    except ImportError:
        return False
    for value in vars(community_service).values():
        if isinstance(value, type) and callable(getattr(value, "publish_album_show", None)):
            return True
    return callable(getattr(community_service, "publish_album_show", None))


async def show_posts(client: AsyncClient, headers: dict[str, str], title: str) -> list[dict[str, object]]:
    response = await client.get(
        "/api/v1/community/post",
        headers=headers,
        params={"tab": "recommend", "q": title, "page": 1, "page_size": 20},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert isinstance(items, list)
    return [item for item in items if item["title"] == title and item["board"] == "show"]


async def test_album_requires_a_token() -> None:
    async with api() as client:
        response = await client.get("/api/v1/album")

    assert_error(response, 401, "UNAUTHORIZED", "Authentication required")


async def test_create_private_album_trims_text_and_defaults() -> None:
    async with api() as client:
        headers = bearer(await login(client))
        payload = write_album(title="  周末出门  ", body="  去公园晒太阳  ", cover_url="")
        del payload["tag_names"]
        created = await client.post("/api/v1/album", headers=headers, json=payload)
        assert created.status_code == 200
        album = created.json()["data"]
        assert_album(
            album,
            title="周末出门",
            body="去公园晒太阳",
            image_urls=["https://example.com/1.jpg"],
            cover_url="https://example.com/1.jpg",
            tag_names=[],
            visibility="private",
            sync_to_forum=False,
        )
        empty = await client.post(
            "/api/v1/album",
            headers=headers,
            json=write_album(title="  ", visibility="nope"),
        )
        assert_error(empty, 400, "VALIDATION", "标题和说明不能为空")
        bad_visibility = await client.post(
            "/api/v1/album",
            headers=headers,
            json=write_album(visibility="secret"),
        )
        assert_error(bad_visibility, 400, "VALIDATION", "可见性不正确")
        patched = await client.patch(
            f"/api/v1/album/{album['id']}",
            headers=headers,
            json={
                "title": " 新标题 ",
                "body": " 新说明 ",
                "image_urls": ["https://example.com/3.jpg", "https://example.com/4.jpg"],
                "cover_url": "https://example.com/cover.jpg",
                "tag_names": ["风景"],
                "visibility": "friends",
            },
        )
        assert patched.status_code == 200
        assert_album(
            patched.json()["data"],
            id=album["id"],
            title="新标题",
            body="新说明",
            image_urls=["https://example.com/3.jpg", "https://example.com/4.jpg"],
            cover_url="https://example.com/cover.jpg",
            tag_names=["风景"],
            visibility="friends",
            sync_to_forum=False,
            created_at=album["created_at"],
        )
        blank_title = await client.patch(
            f"/api/v1/album/{album['id']}",
            headers=headers,
            json={"title": "  "},
        )
        assert_error(blank_title, 400, "VALIDATION", "标题不能为空")
        blank_body = await client.patch(
            f"/api/v1/album/{album['id']}",
            headers=headers,
            json={"body": ""},
        )
        assert_error(blank_body, 400, "VALIDATION", "说明不能为空")
        current = await client.get(f"/api/v1/album/{album['id']}", headers=headers)
        assert current.status_code == 200
        assert current.json()["data"]["title"] == "新标题"
        assert current.json()["data"]["body"] == "新说明"


async def test_public_sync_keeps_album_and_publishes_when_available() -> None:
    title = f"晒太阳-{uuid.uuid4()}"
    async with api() as client:
        token = await login(client)
        headers = bearer(token)
        created = await client.post(
            "/api/v1/album",
            headers=headers,
            json=write_album(
                title=title,
                body="公园",
                image_urls=["https://example.com/1.jpg", "https://example.com/2.jpg"],
                tag_names=["生活", "风景"],
                visibility="public",
                sync_to_forum=True,
            ),
        )
        assert created.status_code == 200
        album = created.json()["data"]
        assert_album(
            album,
            title=title,
            body="公园",
            visibility="public",
            sync_to_forum=True,
            cover_url="https://example.com/1.jpg",
            tag_names=["生活", "风景"],
        )
        fetched = await client.get(f"/api/v1/album/{album['id']}", headers=headers)
        assert fetched.status_code == 200
        assert fetched.json()["data"]["id"] == album["id"]
        renamed = await client.patch(
            f"/api/v1/album/{album['id']}",
            headers=headers,
            json={"body": "还在公园"},
        )
        assert renamed.status_code == 200
        assert renamed.json()["data"]["sync_to_forum"] is True
        if publish_album_show_ready():
            posts = await show_posts(client, headers, title)
            assert len(posts) == 1
            assert posts[0]["status"] == "published"
            assert posts[0]["author"]["id"] == decode_access_token(token)
            assert posts[0]["image_urls"] == album["image_urls"]
            assert posts[0]["body"] == "公园"
            assert posts[0]["topic_names"] == ["生活", "风景"]


async def test_patch_can_turn_sync_on_for_a_public_album() -> None:
    title = f"改公开-{uuid.uuid4()}"
    async with api() as client:
        token = await login(client)
        headers = bearer(token)
        created = await client.post(
            "/api/v1/album",
            headers=headers,
            json=write_album(title=title, visibility="public", sync_to_forum=False),
        )
        assert created.status_code == 200
        album_id = created.json()["data"]["id"]
        synced = await client.patch(
            f"/api/v1/album/{album_id}",
            headers=headers,
            json={"sync_to_forum": True},
        )
        assert synced.status_code == 200
        assert synced.json()["data"]["visibility"] == "public"
        assert synced.json()["data"]["sync_to_forum"] is True
        if publish_album_show_ready():
            posts = await show_posts(client, headers, title)
            assert len(posts) == 1
            assert posts[0]["status"] == "published"
            assert posts[0]["author"]["id"] == decode_access_token(token)


@pytest.mark.parametrize("visibility", ["private", "friends", None])
async def test_reject_sync_on_a_non_public_album(visibility: str | None) -> None:
    async with api() as client:
        headers = bearer(await login(client))
        payload = write_album(sync_to_forum=True)
        if visibility is None:
            payload.pop("visibility", None)
        else:
            payload["visibility"] = visibility
        rejected = await client.post("/api/v1/album", headers=headers, json=payload)
        assert_error(rejected, 400, "VALIDATION", "只有公开相册可以同步到广场")
        listed = await client.get("/api/v1/album", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["data"]["total"] == 0


async def test_patch_cannot_sync_a_private_album() -> None:
    async with api() as client:
        headers = bearer(await login(client))
        created = await client.post("/api/v1/album", headers=headers, json=write_album())
        album_id = created.json()["data"]["id"]
        rejected = await client.patch(
            f"/api/v1/album/{album_id}",
            headers=headers,
            json={"sync_to_forum": True},
        )
        assert_error(rejected, 400, "VALIDATION", "只有公开相册可以同步到广场")
        current = await client.get(f"/api/v1/album/{album_id}", headers=headers)
        assert current.json()["data"]["visibility"] == "private"
        assert current.json()["data"]["sync_to_forum"] is False


@pytest.mark.parametrize("visibility", ["private", "friends"])
async def test_reject_dropping_visibility_on_a_synced_public_album(visibility: str) -> None:
    async with api() as client:
        headers = bearer(await login(client))
        created = await client.post(
            "/api/v1/album",
            headers=headers,
            json=write_album(visibility="public", sync_to_forum=True, title=f"已同步-{uuid.uuid4()}"),
        )
        assert created.status_code == 200
        album_id = created.json()["data"]["id"]
        rejected = await client.patch(
            f"/api/v1/album/{album_id}",
            headers=headers,
            json={"visibility": visibility, "sync_to_forum": False},
        )
        assert_error(rejected, 400, "VALIDATION", "已同步的公开相册不能改为非公开")
        current = await client.get(f"/api/v1/album/{album_id}", headers=headers)
        assert current.status_code == 200
        assert current.json()["data"]["visibility"] == "public"
        assert current.json()["data"]["sync_to_forum"] is True


async def test_other_user_get_is_hidden_and_writes_are_forbidden() -> None:
    async with api() as client:
        owner = bearer(await login(client))
        other = bearer(await login(client))
        created = await client.post(
            "/api/v1/album",
            headers=owner,
            json=write_album(title="别人的相册", visibility="public"),
        )
        album_id = created.json()["data"]["id"]
        seen = await client.get(f"/api/v1/album/{album_id}", headers=other)
        assert_error(seen, 404, "NOT_FOUND", "相册不存在")
        assert "别人的相册" not in seen.text
        updated = await client.patch(
            f"/api/v1/album/{album_id}",
            headers=other,
            json={"title": "改掉"},
        )
        assert updated.status_code == 403
        assert updated.json()["error"]["code"] == "FORBIDDEN"
        deleted = await client.delete(f"/api/v1/album/{album_id}", headers=other)
        assert deleted.status_code == 403
        assert deleted.json()["error"]["code"] == "FORBIDDEN"
        current = await client.get(f"/api/v1/album/{album_id}", headers=owner)
        assert current.status_code == 200
        assert current.json()["data"]["title"] == "别人的相册"


async def test_image_count_limits() -> None:
    async with api() as client:
        headers = bearer(await login(client))
        empty = await client.post("/api/v1/album", headers=headers, json=write_album(image_urls=[]))
        assert_error(empty, 400, "VALIDATION", "至少上传一张照片")
        too_many = await client.post(
            "/api/v1/album",
            headers=headers,
            json=write_album(image_urls=urls(10)),
        )
        assert_error(too_many, 400, "VALIDATION", "最多 9 张照片")
        created = await client.post(
            "/api/v1/album",
            headers=headers,
            json=write_album(image_urls=urls(9)),
        )
        assert created.status_code == 200
        album = created.json()["data"]
        assert len(album["image_urls"]) == 9
        assert album["cover_url"] == album["image_urls"][0]
        cleared = await client.patch(
            f"/api/v1/album/{album['id']}",
            headers=headers,
            json={"image_urls": []},
        )
        assert_error(cleared, 400, "VALIDATION", PHOTO_COUNT)
        oversized = await client.patch(
            f"/api/v1/album/{album['id']}",
            headers=headers,
            json={"image_urls": urls(10)},
        )
        assert_error(oversized, 400, "VALIDATION", PHOTO_COUNT)
        current = await client.get(f"/api/v1/album/{album['id']}", headers=headers)
        assert current.json()["data"]["image_urls"] == urls(9)


async def test_list_is_only_the_current_user_and_paginates() -> None:
    async with api() as client:
        owner = bearer(await login(client))
        other = bearer(await login(client))
        foreign = await client.post(
            "/api/v1/album",
            headers=other,
            json=write_album(title="他人相册", visibility="public"),
        )
        assert foreign.status_code == 200
        foreign_id = foreign.json()["data"]["id"]
        first = await client.post(
            "/api/v1/album",
            headers=owner,
            json=write_album(title="较早", visibility="private"),
        )
        second = await client.post(
            "/api/v1/album",
            headers=owner,
            json=write_album(title="较新", visibility="friends", tag_names=[]),
        )
        assert first.status_code == 200
        assert second.status_code == 200
        first_id = first.json()["data"]["id"]
        second_id = second.json()["data"]["id"]
        listed = await client.get("/api/v1/album", headers=owner)
        assert listed.status_code == 200
        page = listed.json()["data"]
        assert set(page) == PAGE_FIELDS
        assert page["page"] == 1
        assert page["page_size"] == 20
        assert page["total"] == 2
        assert [item["id"] for item in page["items"]] == [second_id, first_id]
        assert foreign_id not in {item["id"] for item in page["items"]}
        narrowed = await client.get(
            "/api/v1/album",
            headers=owner,
            params={"page": 1, "page_size": 1},
        )
        first_page = narrowed.json()["data"]
        assert set(first_page) == PAGE_FIELDS
        assert first_page["total"] == 2
        assert first_page["page"] == 1
        assert first_page["page_size"] == 1
        assert [item["id"] for item in first_page["items"]] == [second_id]
        next_page = await client.get(
            "/api/v1/album",
            headers=owner,
            params={"page": 2, "page_size": 1},
        )
        assert [item["id"] for item in next_page.json()["data"]["items"]] == [first_id]
        other_list = await client.get("/api/v1/album", headers=other)
        other_ids = {item["id"] for item in other_list.json()["data"]["items"]}
        assert other_ids == {foreign_id}
        removed = await client.delete(f"/api/v1/album/{second_id}", headers=owner)
        assert removed.status_code == 200
        assert removed.json() == {"data": {"ok": True}}
        missing = await client.get(f"/api/v1/album/{second_id}", headers=owner)
        assert_error(missing, 404, "NOT_FOUND", "相册不存在")


async def test_missing_album_is_not_found() -> None:
    missing_id = str(uuid.uuid4())
    async with api() as client:
        headers = bearer(await login(client))
        for path in (missing_id, "not-a-uuid"):
            fetched = await client.get(f"/api/v1/album/{path}", headers=headers)
            assert_error(fetched, 404, "NOT_FOUND", "相册不存在")
            updated = await client.patch(
                f"/api/v1/album/{path}",
                headers=headers,
                json={"title": "不存在"},
            )
            assert_error(updated, 404, "NOT_FOUND", "相册不存在")
            deleted = await client.delete(f"/api/v1/album/{path}", headers=headers)
            assert_error(deleted, 404, "NOT_FOUND", "相册不存在")
