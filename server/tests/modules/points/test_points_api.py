import re
import uuid
from datetime import date, datetime, time, timedelta

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.core.clock import APP_ZONE, today_local
from app.core.db import SessionFactory
from app.core.exceptions import AppError, ErrorCode
from app.core.security import create_access_token, decode_access_token
from app.main import create_app
from app.modules.points.models import PointsCard, PointsCheckin, PointsEntry
from app.modules.points.repository import PointsRepository
from app.modules.points.service import PointsService


STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
SUMMARY_FIELDS = {
    "earned",
    "spent",
    "balance",
    "streak",
    "makeup_card_count",
    "today_checked",
    "makeup_dates",
    "checkin_dates",
    "today_post_count",
    "today_comment_count",
    "today_like_count",
}
CHECKIN_FIELDS = {
    "awarded",
    "balance",
    "already_done",
    "date",
    "streak",
    "extra",
    "makeup_cards_awarded",
    "makeup_card_count",
}
MAKEUP_FIELDS = {"awarded", "balance", "date", "streak", "makeup_card_count"}
ENTRY_FIELDS = {"id", "kind", "amount", "title", "balance_after", "created_at"}


def api() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def user_id_of(token: str) -> uuid.UUID:
    return uuid.UUID(decode_access_token(token))


def recent_days(today: date, start: int, stop: int) -> list[date]:
    return [today - timedelta(days=offset) for offset in range(start, stop)]


def quarter_start(today: date) -> date:
    month = today.month - 2
    year = today.year
    if month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


def noon(day: date) -> datetime:
    return datetime.combine(day, time(12, 0), tzinfo=APP_ZONE)


async def login(client: AsyncClient, code: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"code": code})
    assert response.status_code == 200
    return response.json()["data"]["token"]


async def seed(user_id: uuid.UUID, days: list[date], cards: int | None = None) -> None:
    async with SessionFactory() as session:
        for day in days:
            session.add(PointsCheckin(user_id=user_id, local_date=day, source="checkin"))
        if cards is not None:
            session.add(PointsCard(user_id=user_id, makeup_card_count=cards))
        await session.commit()


async def load_entries(user_id: uuid.UUID) -> list[PointsEntry]:
    async with SessionFactory() as session:
        rows = await session.scalars(
            select(PointsEntry)
            .where(PointsEntry.user_id == user_id)
            .order_by(PointsEntry.created_at.asc(), PointsEntry.id.asc())
        )
        return list(rows.all())


async def test_summary_after_registration() -> None:
    async with api() as client:
        token = await login(client, "points-summary")
        today = today_local()
        response = await client.get("/api/v1/points/summary", headers=bearer(token))

    assert response.status_code == 200
    assert set(response.json()) == {"data"}
    data = response.json()["data"]
    assert set(data) == SUMMARY_FIELDS
    assert data["earned"] == 100
    assert data["spent"] == 0
    assert data["balance"] == 100
    assert data["streak"] == 0
    assert data["makeup_card_count"] == 0
    assert data["today_checked"] is False
    assert data["makeup_dates"] == [day.isoformat() for day in recent_days(today, 1, 7)]
    assert data["checkin_dates"] == []
    assert data["today_post_count"] == 0
    assert data["today_comment_count"] == 0
    assert data["today_like_count"] == 0


async def test_checkin_awards_ten_then_repeat_is_already_done() -> None:
    async with api() as client:
        token = await login(client, "points-checkin")
        headers = bearer(token)
        user_id = user_id_of(token)
        today = today_local()
        first = await client.post("/api/v1/points/checkin", headers=headers, json={})
        second = await client.post("/api/v1/points/checkin", headers=headers, json={})
        summary = await client.get("/api/v1/points/summary", headers=headers)

    assert first.status_code == 200
    body = first.json()["data"]
    assert set(body) == CHECKIN_FIELDS
    assert body["awarded"] == 10
    assert body["balance"] == 110
    assert body["already_done"] is False
    assert body["date"] == today.isoformat()
    assert body["streak"] == 1
    assert body["extra"] == 0
    assert body["makeup_cards_awarded"] == 0
    assert body["makeup_card_count"] == 0

    assert second.status_code == 200
    again = second.json()["data"]
    assert again["awarded"] == 0
    assert again["already_done"] is True
    assert again["extra"] == 0
    assert again["makeup_cards_awarded"] == 0
    assert again["balance"] == 110
    assert again["streak"] == 1
    assert again["date"] == today.isoformat()
    assert again["makeup_card_count"] == 0

    rows = await load_entries(user_id)
    assert len(rows) == 2
    assert {row.title for row in rows} == {"注册", "签到"}
    checkin = next(row for row in rows if row.title == "签到")
    assert checkin.kind == "earn"
    assert checkin.amount == 10
    assert checkin.balance_after == 110
    assert checkin.event_key == f"checkin:{user_id}:{today.isoformat()}"

    data = summary.json()["data"]
    assert data["earned"] == 110
    assert data["spent"] == 0
    assert data["balance"] == 110
    assert data["streak"] == 1
    assert data["today_checked"] is True
    assert data["makeup_card_count"] == 0
    assert data["makeup_dates"] == [day.isoformat() for day in recent_days(today, 1, 7)]
    assert data["checkin_dates"] == [today.isoformat()]


async def test_makeup_validation_messages() -> None:
    async with api() as client:
        token = await login(client, "points-makeup-invalid")
        headers = bearer(token)
        user_id = user_id_of(token)
        today = today_local()
        yesterday = today - timedelta(days=1)

        invalid = await client.post("/api/v1/points/makeup", headers=headers, json={"date": "nope"})
        not_today = await client.post(
            "/api/v1/points/makeup",
            headers=headers,
            json={"date": today.isoformat()},
        )
        no_card = await client.post(
            "/api/v1/points/makeup",
            headers=headers,
            json={"date": yesterday.isoformat()},
        )
        number = await client.post("/api/v1/points/makeup", headers=headers, json={"date": 20260901})
        empty = await client.post("/api/v1/points/makeup", headers=headers, json={"date": None})
        await seed(user_id, [yesterday], cards=1)
        already = await client.post(
            "/api/v1/points/makeup",
            headers=headers,
            json={"date": yesterday.isoformat()},
        )
        too_old = await client.post(
            "/api/v1/points/makeup",
            headers=headers,
            json={"date": (today - timedelta(days=7)).isoformat()},
        )
        future = await client.post(
            "/api/v1/points/makeup",
            headers=headers,
            json={"date": (today + timedelta(days=1)).isoformat()},
        )
        impossible = await client.post(
            "/api/v1/points/makeup",
            headers=headers,
            json={"date": "2026-02-31"},
        )
        still_today = await client.post(
            "/api/v1/points/makeup",
            headers=headers,
            json={"date": today.isoformat()},
        )

    cases = [
        (invalid, "日期无效"),
        (number, "日期无效"),
        (empty, "日期无效"),
        (not_today, "不能补今天"),
        (still_today, "不能补今天"),
        (no_card, "无法补签"),
        (already, "这一天已经签过到了"),
        (too_old, "不在可补签范围内"),
        (future, "不在可补签范围内"),
        (impossible, "不在可补签范围内"),
    ]
    for response, message in cases:
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION"
        assert response.json()["error"]["message"] == message

    rows = await load_entries(user_id)
    assert [row.title for row in rows] == ["注册"]
    async with SessionFactory() as session:
        card = await session.get(PointsCard, user_id)
    assert card is not None
    assert card.makeup_card_count == 1


async def test_makeup_fills_a_gap_without_the_streak_bonus() -> None:
    async with api() as client:
        token = await login(client, "points-makeup-gap")
        headers = bearer(token)
        user_id = user_id_of(token)
        today = today_local()
        yesterday = today - timedelta(days=1)
        await seed(user_id, recent_days(today, 2, 4), cards=1)
        made_up = await client.post(
            "/api/v1/points/makeup",
            headers=headers,
            json={"date": yesterday.isoformat()},
        )
        checked = await client.post("/api/v1/points/checkin", headers=headers, json={})

    assert made_up.status_code == 200
    body = made_up.json()["data"]
    assert set(body) == MAKEUP_FIELDS
    assert body["awarded"] == 10
    assert body["balance"] == 110
    assert body["date"] == yesterday.isoformat()
    assert body["streak"] == 3
    assert body["makeup_card_count"] == 0

    assert checked.status_code == 200
    today_body = checked.json()["data"]
    assert today_body["awarded"] == 10
    assert today_body["extra"] == 0
    assert today_body["makeup_cards_awarded"] == 0
    assert today_body["streak"] == 4
    assert today_body["balance"] == 120
    assert today_body["makeup_card_count"] == 0

    rows = await load_entries(user_id)
    assert {row.title for row in rows} == {"注册", "补签", "签到"}
    makeup = next(row for row in rows if row.title == "补签")
    assert makeup.amount == 10
    assert makeup.balance_after == 110
    assert makeup.event_key == f"makeup:{user_id}:{yesterday.isoformat()}"
    async with SessionFactory() as session:
        stored = await session.scalar(
            select(PointsCheckin).where(
                PointsCheckin.user_id == user_id,
                PointsCheckin.local_date == yesterday,
            )
        )
    assert stored is not None
    assert stored.source == "makeup"


async def test_makeup_accepts_the_oldest_open_day() -> None:
    async with api() as client:
        token = await login(client, "points-makeup-edge")
        headers = bearer(token)
        user_id = user_id_of(token)
        today = today_local()
        day = today - timedelta(days=6)
        await seed(user_id, [], cards=1)
        response = await client.post("/api/v1/points/makeup", headers=headers, json={"date": day.isoformat()})
        summary = await client.get("/api/v1/points/summary", headers=headers)

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["awarded"] == 10
    assert body["balance"] == 110
    assert body["date"] == day.isoformat()
    assert body["streak"] == 0
    assert body["makeup_card_count"] == 0
    data = summary.json()["data"]
    assert day.isoformat() in data["checkin_dates"]
    assert day.isoformat() not in data["makeup_dates"]
    assert data["today_checked"] is False


async def test_third_day_checkin_awards_bonus_and_a_card() -> None:
    async with api() as client:
        token = await login(client, "points-streak-3")
        headers = bearer(token)
        user_id = user_id_of(token)
        today = today_local()
        await seed(user_id, recent_days(today, 1, 3))
        response = await client.post("/api/v1/points/checkin", headers=headers, json={})
        summary = await client.get("/api/v1/points/summary", headers=headers)
        ledger = await client.get("/api/v1/points/ledger", headers=headers)

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["awarded"] == 30
    assert body["extra"] == 20
    assert body["balance"] == 130
    assert body["already_done"] is False
    assert body["date"] == today.isoformat()
    assert body["streak"] == 3
    assert body["makeup_cards_awarded"] == 1
    assert body["makeup_card_count"] == 1

    rows = await load_entries(user_id)
    assert {row.title for row in rows} == {"注册", "签到", "连续签到奖励"}
    by_title = {row.title: row for row in rows}
    assert by_title["签到"].amount == 10
    assert by_title["签到"].balance_after == 110
    assert by_title["签到"].event_key == f"checkin:{user_id}:{today.isoformat()}"
    assert by_title["连续签到奖励"].amount == 20
    assert by_title["连续签到奖励"].balance_after == 130
    assert by_title["连续签到奖励"].event_key == f"checkin-bonus:{user_id}:{today.isoformat()}"

    data = summary.json()["data"]
    assert data["earned"] == 130
    assert data["spent"] == 0
    assert data["balance"] == 130
    assert data["streak"] == 3
    assert data["makeup_card_count"] == 1
    assert data["today_checked"] is True
    signed = {day.isoformat() for day in [today, *recent_days(today, 1, 3)]}
    assert set(data["checkin_dates"]) == signed
    assert data["makeup_dates"] == [day.isoformat() for day in recent_days(today, 3, 7)]
    assert "event_key" not in ledger.text


async def test_seventh_day_checkin_awards_the_larger_bonus() -> None:
    async with api() as client:
        token = await login(client, "points-streak-7")
        headers = bearer(token)
        user_id = user_id_of(token)
        today = today_local()
        await seed(user_id, recent_days(today, 1, 7))
        response = await client.post("/api/v1/points/checkin", headers=headers, json={})

    body = response.json()["data"]
    assert response.status_code == 200
    assert body["awarded"] == 60
    assert body["extra"] == 50
    assert body["balance"] == 160
    assert body["streak"] == 7
    assert body["makeup_cards_awarded"] == 1
    assert body["makeup_card_count"] == 1
    rows = await load_entries(user_id)
    bonus = next(row for row in rows if row.title == "连续签到奖励")
    assert bonus.amount == 50
    assert bonus.balance_after == 160
    assert bonus.event_key == f"checkin-bonus:{user_id}:{today.isoformat()}"


async def test_eighth_day_checkin_is_only_ten() -> None:
    async with api() as client:
        token = await login(client, "points-streak-8")
        headers = bearer(token)
        user_id = user_id_of(token)
        today = today_local()
        await seed(user_id, recent_days(today, 1, 8))
        response = await client.post("/api/v1/points/checkin", headers=headers, json={})

    body = response.json()["data"]
    assert response.status_code == 200
    assert body["awarded"] == 10
    assert body["extra"] == 0
    assert body["balance"] == 110
    assert body["streak"] == 8
    assert body["makeup_cards_awarded"] == 0
    assert body["makeup_card_count"] == 0
    rows = await load_entries(user_id)
    assert {row.title for row in rows} == {"注册", "签到"}


async def test_spend_below_balance_leaves_it_unchanged() -> None:
    async with api() as client:
        token = await login(client, "points-spend-short")
    user_id = user_id_of(token)
    async with SessionFactory() as session:
        service = PointsService(PointsRepository(session))
        with pytest.raises(AppError) as caught:
            await service.spend(user_id, 101, "兑换", "spend:short")
        assert await service.balance(user_id) == 100

    error = caught.value
    assert error.code == ErrorCode.POINTS_NOT_ENOUGH
    assert error.status_code == 409
    assert error.message == "积分不足"
    rows = await load_entries(user_id)
    assert len(rows) == 1
    assert rows[0].balance_after == 100
    assert rows[0].title == "注册"


async def test_spend_can_use_the_full_balance_once() -> None:
    async with api() as client:
        token = await login(client, "points-spend-all")
    user_id = user_id_of(token)
    async with SessionFactory() as session:
        service = PointsService(PointsRepository(session))
        await service.spend(user_id, 100, "图生视频", "video:once")
        await service.spend(user_id, 100, "图生视频", "video:once")
        assert await service.balance(user_id) == 0
        await session.commit()

    rows = await load_entries(user_id)
    spends = [row for row in rows if row.kind == "spend"]
    assert len(spends) == 1
    assert spends[0].amount == 100
    assert spends[0].title == "图生视频"
    assert spends[0].balance_after == 0
    assert spends[0].event_key == "video:once"


async def test_daily_awards_stop_at_the_cap() -> None:
    async with api() as client:
        token = await login(client, "points-awards")
        user_id = user_id_of(token)
        async with SessionFactory() as session:
            service = PointsService(PointsRepository(session))
            for _ in range(4):
                await service.award_published_post(user_id)
            for _ in range(2):
                await service.award_comment(user_id)
            for _ in range(4):
                await service.award_like(user_id)
            await session.commit()
        summary = await client.get("/api/v1/points/summary", headers=bearer(token))

    rows = await load_entries(user_id)
    posts = [row for row in rows if row.title == "发布帖子"]
    comments = [row for row in rows if row.title == "评论"]
    likes = [row for row in rows if row.title == "点赞"]
    today = today_local().isoformat()
    assert len(posts) == 3
    assert {row.amount for row in posts} == {20}
    assert {row.event_key for row in posts} == {
        f"post:{user_id}:{today}:1",
        f"post:{user_id}:{today}:2",
        f"post:{user_id}:{today}:3",
    }
    assert len(comments) == 1
    assert comments[0].amount == 5
    assert comments[0].event_key == f"comment:{user_id}:{today}"
    assert len(likes) == 3
    assert {row.amount for row in likes} == {2}
    assert {row.event_key for row in likes} == {
        f"like:{user_id}:{today}:1",
        f"like:{user_id}:{today}:2",
        f"like:{user_id}:{today}:3",
    }
    data = summary.json()["data"]
    assert data["today_post_count"] == 3
    assert data["today_comment_count"] == 1
    assert data["today_like_count"] == 3
    assert data["earned"] == 171
    assert data["spent"] == 0
    assert data["balance"] == 171


async def test_ledger_filters_kind_and_range() -> None:
    async with api() as client:
        token = await login(client, "points-ledger")
        headers = bearer(token)
        user_id = user_id_of(token)
        today = today_local()
        start = quarter_start(today)
        async with SessionFactory() as session:
            service = PointsService(PointsRepository(session))
            await service.spend(user_id, 10, "兑换", f"spend:ledger:{user_id}")
            session.add(
                PointsEntry(
                    user_id=user_id,
                    kind="earn",
                    amount=1,
                    title="季度",
                    balance_after=1,
                    event_key=f"ledger-quarter:{user_id}",
                    created_at=noon(start),
                )
            )
            session.add(
                PointsEntry(
                    user_id=user_id,
                    kind="earn",
                    amount=1,
                    title="更早",
                    balance_after=1,
                    event_key=f"ledger-old:{user_id}",
                    created_at=noon(start - timedelta(days=1)),
                )
            )
            await session.commit()

        everything = await client.get("/api/v1/points/ledger", headers=headers)
        blank_filters = await client.get(
            "/api/v1/points/ledger",
            headers=headers,
            params={"kind": "", "range": ""},
        )
        month = await client.get("/api/v1/points/ledger", headers=headers, params={"range": "month"})
        quarter = await client.get("/api/v1/points/ledger", headers=headers, params={"range": "quarter"})
        earns = await client.get("/api/v1/points/ledger", headers=headers, params={"kind": "earn"})
        spends = await client.get("/api/v1/points/ledger", headers=headers, params={"kind": "spend"})
        month_earns = await client.get(
            "/api/v1/points/ledger",
            headers=headers,
            params={"kind": "earn", "range": "month"},
        )
        first_page = await client.get(
            "/api/v1/points/ledger",
            headers=headers,
            params={"page": 1, "page_size": 1},
        )
        bad_kind = await client.get("/api/v1/points/ledger", headers=headers, params={"kind": "gift"})
        bad_range = await client.get("/api/v1/points/ledger", headers=headers, params={"range": "week"})

    def titles(response: object) -> list[str]:
        assert hasattr(response, "json")
        return [item["title"] for item in response.json()["data"]["items"]]

    assert everything.status_code == 200
    body = everything.json()["data"]
    assert set(body) == {"items", "total", "page", "page_size"}
    assert body["total"] == 4
    assert body["page"] == 1
    assert body["page_size"] == 20
    assert titles(everything) == ["兑换", "注册", "季度", "更早"]
    assert titles(blank_filters) == ["兑换", "注册", "季度", "更早"]
    assert titles(month) == ["兑换", "注册"]
    assert titles(quarter) == ["兑换", "注册", "季度"]
    assert titles(earns) == ["注册", "季度", "更早"]
    assert titles(spends) == ["兑换"]
    assert titles(month_earns) == ["注册"]
    assert titles(first_page) == ["兑换"]
    assert first_page.json()["data"]["total"] == 4
    assert first_page.json()["data"]["page_size"] == 1

    spend = spends.json()["data"]["items"][0]
    assert set(spend) == ENTRY_FIELDS
    assert spend["kind"] == "spend"
    assert spend["amount"] == 10
    assert spend["balance_after"] == 90
    assert STAMP.fullmatch(spend["created_at"])
    uuid.UUID(spend["id"])
    assert "event_key" not in everything.text

    assert bad_kind.status_code == 400
    assert bad_kind.json()["error"]["code"] == "VALIDATION"
    assert bad_range.status_code == 400
    assert bad_range.json()["error"]["code"] == "VALIDATION"


@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("GET", "/api/v1/points/summary", None),
        ("GET", "/api/v1/points/ledger", None),
        ("POST", "/api/v1/points/checkin", {}),
        ("POST", "/api/v1/points/makeup", {"date": "2026-09-01"}),
    ],
)
async def test_points_routes_require_a_token(method: str, path: str, payload: dict[str, str] | None) -> None:
    async with api() as client:
        response = await client.request(method, path, json=payload)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_bad_token_is_unauthorized() -> None:
    async with api() as client:
        response = await client.get(
            "/api/v1/points/summary",
            headers=bearer(create_access_token("not-a-uuid")),
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
