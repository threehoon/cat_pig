import asyncio

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.db import SessionFactory
from app.main import create_app
from app.modules.auth.repository import UserRepository
from app.modules.points.models import PointsEntry


def api() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


async def fetch_entries() -> list[PointsEntry]:
    async with SessionFactory() as session:
        rows = await session.scalars(select(PointsEntry).order_by(PointsEntry.created_at))
        return list(rows.all())


async def test_existing_user_is_credited_once_on_next_login() -> None:
    async with SessionFactory() as session:
        user = await UserRepository(session).upsert_by_openid("local:already")
        await session.commit()
        user_id = user.id

    async with api() as client:
        first = await client.post("/api/v1/auth/login", json={"code": "already"})
        second = await client.post("/api/v1/auth/login", json={"code": "already"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert "points_balance" not in first.text
    entries = await fetch_entries()
    assert len(entries) == 1
    assert entries[0].user_id == user_id
    assert entries[0].kind == "earn"
    assert entries[0].amount == 100
    assert entries[0].title == "注册"
    assert entries[0].balance_after == 100
    assert entries[0].event_key == f"register:{user_id}"


async def test_two_codes_each_receive_one_registration_entry() -> None:
    async with api() as client:
        first = await client.post("/api/v1/auth/login", json={"code": "alpha"})
        second = await client.post("/api/v1/auth/login", json={"code": "beta"})

    assert first.status_code == 200
    assert second.status_code == 200
    entries = await fetch_entries()
    assert len(entries) == 2
    assert len({entry.user_id for entry in entries}) == 2
    assert {entry.amount for entry in entries} == {100}
    assert {entry.balance_after for entry in entries} == {100}
    assert {entry.title for entry in entries} == {"注册"}
    assert {entry.kind for entry in entries} == {"earn"}


async def test_concurrent_login_writes_one_registration() -> None:
    async with api() as client:
        first, second = await asyncio.gather(
            client.post("/api/v1/auth/login", json={"code": "concurrent-points"}),
            client.post("/api/v1/auth/login", json={"code": "concurrent-points"}),
        )

    assert first.status_code == 200
    assert second.status_code == 200
    entries = await fetch_entries()
    assert len(entries) == 1
    assert entries[0].amount == 100
    assert entries[0].balance_after == 100
    assert entries[0].event_key == f"register:{entries[0].user_id}"
