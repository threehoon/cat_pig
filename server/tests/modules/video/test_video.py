import re
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

from app.core.clock import today_local
from app.core.db import SessionFactory
from app.main import create_app
from app.modules.video.models import VideoTask


VIDEO_FIELDS = {
    "id",
    "title",
    "image_urls",
    "prompt",
    "resolution",
    "status",
    "result_url",
    "points_cost",
    "error_message",
    "created_at",
}
CREATED_AT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
TWO_IMAGES = ["https://example.com/1.jpg", "https://example.com/2.jpg"]
NINE_IMAGES = [f"https://example.com/{index}.jpg" for index in range(9)]


def api() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def video_body(**overrides: object) -> dict[str, object]:
    body: dict[str, object] = {
        "title": "周末成长视频",
        "image_urls": list(TWO_IMAGES),
        "prompt": "草地上跑",
        "resolution": "720p",
    }
    body.update(overrides)
    return body


async def login(client: AsyncClient, code: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"code": code})
    assert response.status_code == 200
    return response.json()["data"]["token"]


async def balance(client: AsyncClient, headers: dict[str, str]) -> int:
    response = await client.get("/api/v1/me", headers=headers)
    assert response.status_code == 200
    return response.json()["data"]["points_balance"]


async def set_status(video_id: str, status: str) -> None:
    async with SessionFactory() as session:
        result = await session.execute(
            update(VideoTask).where(VideoTask.id == uuid.UUID(video_id)).values(status=status)
        )
        await session.commit()
    assert result.rowcount == 1


def assert_video(data: dict[str, object], **expected: object) -> None:
    assert set(data) == VIDEO_FIELDS
    assert isinstance(data["id"], str)
    uuid.UUID(data["id"])
    assert data["status"] == "pending"
    assert data["result_url"] is None
    assert data["error_message"] is None
    assert data["points_cost"] == 50
    assert isinstance(data["created_at"], str)
    assert CREATED_AT.fullmatch(data["created_at"])
    for key, value in expected.items():
        assert data[key] == value


async def test_video_requires_a_token() -> None:
    async with api() as client:
        listed = await client.get("/api/v1/video")
        created = await client.post("/api/v1/video", json=video_body())

    assert listed.status_code == 401
    assert listed.json()["error"]["code"] == "UNAUTHORIZED"
    assert created.status_code == 401
    assert created.json()["error"]["code"] == "UNAUTHORIZED"


async def test_create_spends_until_empty_and_keeps_two_tasks() -> None:
    async with api() as client:
        headers = bearer(await login(client, "video-spend"))
        assert await balance(client, headers) == 100
        first = await client.post(
            "/api/v1/video",
            headers=headers,
            json=video_body(title="  周末成长视频  ", prompt="草" * 100, resolution="720p"),
        )
        assert first.status_code == 200, first.text
        first_body = first.json()["data"]
        balance_after_first = await balance(client, headers)
        fetched = await client.get(f"/api/v1/video/{first_body['id']}", headers=headers)
        second = await client.post(
            "/api/v1/video",
            headers=headers,
            json=video_body(
                title="第二个",
                image_urls=NINE_IMAGES,
                prompt="",
                resolution="1080p",
            ),
        )
        assert second.status_code == 200, second.text
        second_body = second.json()["data"]
        balance_after_second = await balance(client, headers)
        third = await client.post("/api/v1/video", headers=headers, json=video_body(resolution="2k"))
        balance_after_third = await balance(client, headers)
        listed = await client.get("/api/v1/video", headers=headers)
        pending = await client.get("/api/v1/video", headers=headers, params={"status": "pending"})

    assert first.status_code == 200
    assert_video(
        first_body,
        title="周末成长视频",
        image_urls=TWO_IMAGES,
        prompt="草" * 100,
        resolution="720p",
    )
    assert balance_after_first == 50
    assert fetched.status_code == 200
    assert fetched.json()["data"] == first_body
    assert second.status_code == 200
    assert_video(
        second_body,
        title="第二个",
        image_urls=NINE_IMAGES,
        prompt="",
        resolution="1080p",
    )
    assert balance_after_second == 0
    assert third.status_code == 409
    assert third.json()["error"]["code"] == "POINTS_NOT_ENOUGH"
    assert third.json()["error"]["message"] == "积分不足"
    assert balance_after_third == 0
    page = listed.json()["data"]
    assert listed.status_code == 200
    assert set(page) == {"items", "total", "page", "page_size"}
    assert page["total"] == 2
    assert page["page"] == 1
    assert page["page_size"] == 20
    assert [item["id"] for item in page["items"]] == [second_body["id"], first_body["id"]]
    assert pending.status_code == 200
    assert pending.json()["data"]["total"] == 2
    assert [item["status"] for item in pending.json()["data"]["items"]] == ["pending", "pending"]


@pytest.mark.parametrize(
    ("code", "changes", "message"),
    [
        ("bad-resolution", {"resolution": "480p"}, "分辨率不正确"),
        ("bad-resolution-case", {"resolution": "720P"}, "分辨率不正确"),
        ("one-image", {"image_urls": ["https://example.com/1.jpg"]}, "请选择 2–9 张照片"),
        ("zero-images", {"image_urls": []}, "请选择 2–9 张照片"),
        (
            "ten-images",
            {"image_urls": [f"https://example.com/{index}.jpg" for index in range(10)]},
            "请选择 2–9 张照片",
        ),
        ("long-prompt", {"prompt": "字" * 101}, "提示词最多 100 字"),
    ],
)
async def test_invalid_create_does_not_spend_or_insert(
    code: str,
    changes: dict[str, object],
    message: str,
) -> None:
    async with api() as client:
        headers = bearer(await login(client, f"video-invalid-{code}"))
        rejected = await client.post("/api/v1/video", headers=headers, json=video_body(**changes))
        remaining = await balance(client, headers)
        listed = await client.get("/api/v1/video", headers=headers)

    assert rejected.status_code == 400
    assert rejected.json()["error"]["code"] == "VALIDATION"
    assert rejected.json()["error"]["message"] == message
    assert remaining == 100
    assert listed.json()["data"]["total"] == 0


async def test_blank_title_uses_shanghai_date() -> None:
    async with api() as client:
        headers = bearer(await login(client, "video-blank-title"))
        omitted = await client.post(
            "/api/v1/video",
            headers=headers,
            json={
                "image_urls": TWO_IMAGES,
                "resolution": "540p",
            },
        )
        blank = await client.post(
            "/api/v1/video",
            headers=headers,
            json=video_body(title="   ", prompt="", resolution="4k"),
        )

    today = today_local().isoformat()
    assert omitted.status_code == 200
    assert_video(omitted.json()["data"], title=today, prompt="", resolution="540p", image_urls=TWO_IMAGES)
    assert blank.status_code == 200
    assert_video(
        blank.json()["data"],
        title=today,
        prompt="",
        resolution="4k",
        image_urls=TWO_IMAGES,
    )


async def test_list_filters_status_and_hides_other_users() -> None:
    async with api() as client:
        owner = bearer(await login(client, "video-list-owner"))
        other = bearer(await login(client, "video-list-other"))
        first = await client.post(
            "/api/v1/video",
            headers=owner,
            json=video_body(title="先创建", resolution="2k"),
        )
        second = await client.post(
            "/api/v1/video",
            headers=owner,
            json=video_body(title="后创建", resolution="4k"),
        )
        first_id = first.json()["data"]["id"]
        second_id = second.json()["data"]["id"]
        await set_status(second_id, "failed")
        pending = await client.get("/api/v1/video", headers=owner, params={"status": "pending"})
        failed = await client.get("/api/v1/video", headers=owner, params={"status": "failed"})
        everything = await client.get("/api/v1/video", headers=owner, params={"status": ""})
        foreign = await client.get("/api/v1/video", headers=other)
        removed = await client.delete(f"/api/v1/video/{second_id}", headers=owner)
        after_delete = await client.get("/api/v1/video", headers=owner)

    assert first.status_code == 200
    assert second.status_code == 200
    assert [item["id"] for item in pending.json()["data"]["items"]] == [first_id]
    assert pending.json()["data"]["total"] == 1
    assert [item["id"] for item in failed.json()["data"]["items"]] == [second_id]
    assert [item["id"] for item in everything.json()["data"]["items"]] == [second_id, first_id]
    assert foreign.status_code == 200
    assert foreign.json()["data"]["items"] == []
    assert foreign.json()["data"]["total"] == 0
    assert removed.status_code == 200
    assert removed.json() == {"data": {"ok": True}}
    assert [item["id"] for item in after_delete.json()["data"]["items"]] == [first_id]


async def test_other_user_cannot_read_or_delete() -> None:
    async with api() as client:
        owner = bearer(await login(client, "video-owner"))
        other = bearer(await login(client, "video-other"))
        created = await client.post("/api/v1/video", headers=owner, json=video_body())
        video_id = created.json()["data"]["id"]
        foreign_get = await client.get(f"/api/v1/video/{video_id}", headers=other)
        foreign_delete = await client.delete(f"/api/v1/video/{video_id}", headers=other)
        owned = await client.get(f"/api/v1/video/{video_id}", headers=owner)
        removed = await client.delete(f"/api/v1/video/{video_id}", headers=owner)
        missing = await client.get(f"/api/v1/video/{video_id}", headers=owner)
        foreign_after = await client.delete(f"/api/v1/video/{video_id}", headers=other)

    assert created.status_code == 200
    assert foreign_get.status_code == 404
    assert foreign_get.json()["error"]["code"] == "NOT_FOUND"
    assert foreign_delete.status_code == 403
    assert foreign_delete.json()["error"]["code"] == "FORBIDDEN"
    assert owned.status_code == 200
    assert owned.json()["data"]["id"] == video_id
    assert removed.status_code == 200
    assert removed.json() == {"data": {"ok": True}}
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"
    assert foreign_after.status_code == 404
    assert foreign_after.json()["error"]["code"] == "NOT_FOUND"


async def test_missing_video_is_not_found() -> None:
    async with api() as client:
        headers = bearer(await login(client, "video-missing"))
        missing_id = str(uuid.uuid4())
        missing_get = await client.get(f"/api/v1/video/{missing_id}", headers=headers)
        missing_delete = await client.delete(f"/api/v1/video/{missing_id}", headers=headers)
        bad_get = await client.get("/api/v1/video/not-a-uuid", headers=headers)
        bad_delete = await client.delete("/api/v1/video/not-a-uuid", headers=headers)

    assert missing_get.status_code == 404
    assert missing_get.json()["error"]["code"] == "NOT_FOUND"
    assert missing_delete.status_code == 404
    assert missing_delete.json()["error"]["code"] == "NOT_FOUND"
    assert bad_get.status_code == 404
    assert bad_get.json()["error"]["code"] == "NOT_FOUND"
    assert bad_delete.status_code == 404
    assert bad_delete.json()["error"]["code"] == "NOT_FOUND"


async def test_running_task_cannot_be_deleted() -> None:
    async with api() as client:
        headers = bearer(await login(client, "video-running"))
        created = await client.post("/api/v1/video", headers=headers, json=video_body(resolution="2k"))
        video_id = created.json()["data"]["id"]
        await set_status(video_id, "running")
        rejected = await client.delete(f"/api/v1/video/{video_id}", headers=headers)
        current = await client.get(f"/api/v1/video/{video_id}", headers=headers)
        listed = await client.get("/api/v1/video", headers=headers)

    assert created.status_code == 200
    assert created.json()["data"]["status"] == "pending"
    assert rejected.status_code == 409
    assert rejected.json()["error"]["code"] == "CONFLICT"
    assert rejected.json()["error"]["message"] == "生成中不能删除"
    assert current.status_code == 200
    assert current.json()["data"]["id"] == video_id
    assert current.json()["data"]["status"] == "running"
    assert current.json()["data"]["result_url"] is None
    assert [item["id"] for item in listed.json()["data"]["items"]] == [video_id]
