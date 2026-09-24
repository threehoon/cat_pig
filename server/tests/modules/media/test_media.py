from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.db import engine
from app.core.settings import get_settings


# 1x1 RGB PNG. The supplied sample hex had an odd length; IHDR is width 1, height 1.
PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753de"
    "0000000c49444154789c63f8cfc0000003010100c9fe92ef0000000049454e44ae426082"
)
MP3_BYTES = b"not-really-audio"
MEDIA_FIELDS = {"url", "width", "height", "mime"}


@pytest.fixture
def media_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "media"
    monkeypatch.setenv("MEDIA_ROOT", str(root))
    get_settings.cache_clear()
    return root


def api() -> AsyncClient:
    # Clear before the first import so create_app() does not mkdir the developer dir.
    get_settings.cache_clear()
    from app.main import create_app

    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient) -> str:
    response = await client.post("/api/v1/auth/login", json={"code": "media-user"})
    assert response.status_code == 200
    return response.json()["data"]["token"]


async def assert_stored(url: str, payload: bytes, mime: str, width: int, height: int) -> None:
    assert url.startswith("/media/")
    stored_name = url.removeprefix("/media/")
    assert "/" not in stored_name
    path = get_settings().media_root / stored_name
    assert path.is_file()
    assert path.read_bytes() == payload
    async with engine.connect() as connection:
        row = (
            await connection.execute(
                text(
                    """
                    SELECT mime, width, height
                    FROM media_object
                    WHERE stored_name = :stored_name
                    """
                ),
                {"stored_name": stored_name},
            )
        ).one()
    assert tuple(row) == (mime, width, height)


async def test_upload_png(media_root: Path) -> None:
    async with api() as client:
        token = await login(client)
        response = await client.post(
            "/api/v1/media",
            headers=bearer(token),
            files={"file": ("pixel.png", PNG_1X1, "image/png")},
        )

    body = response.json()
    assert response.status_code == 200
    assert set(body) == {"data"}
    assert set(body["data"]) == MEDIA_FIELDS
    assert body["data"]["mime"] == "image/png"
    assert body["data"]["width"] == 1
    assert body["data"]["height"] == 1
    assert body["data"]["url"].endswith(".png")
    assert "pixel.png" not in body["data"]["url"]
    assert get_settings().media_root.resolve() == media_root.resolve()
    await assert_stored(body["data"]["url"], PNG_1X1, "image/png", 1, 1)


async def test_upload_mp3(media_root: Path) -> None:
    async with api() as client:
        token = await login(client)
        response = await client.post(
            "/api/v1/media",
            headers=bearer(token),
            files={"file": ("a.mp3", MP3_BYTES, "audio/mpeg")},
        )

    body = response.json()
    assert response.status_code == 200
    assert set(body) == {"data"}
    assert set(body["data"]) == MEDIA_FIELDS
    assert body["data"]["mime"] == "audio/mpeg"
    assert body["data"]["width"] == 0
    assert body["data"]["height"] == 0
    url = body["data"]["url"]
    assert url.startswith("/media/")
    assert url.endswith(".mp3")
    assert not url.endswith("/a.mp3")
    assert get_settings().media_root.resolve() == media_root.resolve()
    await assert_stored(url, MP3_BYTES, "audio/mpeg", 0, 0)


async def test_missing_token_is_unauthorized(media_root: Path) -> None:
    async with api() as client:
        response = await client.post(
            "/api/v1/media",
            files={"file": ("a.png", PNG_1X1, "image/png")},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
    assert get_settings().media_root.resolve() == media_root.resolve()
    assert list(media_root.glob("*")) == []


async def test_empty_upload_is_rejected(media_root: Path) -> None:
    async with api() as client:
        token = await login(client)
        headers = bearer(token)
        empty = await client.post(
            "/api/v1/media",
            headers=headers,
            files={"file": ("a.png", b"", "image/png")},
        )
        missing = await client.post("/api/v1/media", headers=headers)

    assert empty.status_code == 400
    assert empty.json()["error"]["code"] == "VALIDATION"
    assert empty.json()["error"]["message"] == "请选择文件"
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == "VALIDATION"
    assert missing.json()["error"]["message"] == "请选择文件"
    assert get_settings().media_root.resolve() == media_root.resolve()
    assert list(media_root.glob("*")) == []
