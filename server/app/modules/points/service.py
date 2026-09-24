import uuid
from typing import Literal

from app.core.clock import format_utc, today_local
from app.core.exceptions import AppError, ErrorCode
from app.core.pagination import PageQuery
from app.modules.points.activity import (
    award_comment as award_comment_for,
    award_like as award_like_for,
    award_published_post as award_published_post_for,
    perform_checkin,
    perform_makeup,
    spend as spend_for,
)
from app.modules.points.models import PointsEntry
from app.modules.points.repository import PointsRepository
from app.modules.points.rules import (
    COMMENT_TITLE,
    DAILY_TITLES,
    LIKE_TITLE,
    POST_TITLE,
    current_streak,
    ledger_bounds,
    local_day_bounds,
    missing_makeup_dates,
    normalize_kind,
    normalize_range,
    visible_checkin_dates,
)
from app.modules.points.schemas import (
    CheckinResult,
    MakeupResult,
    PointsEntry as PointsEntryOut,
    PointsEntryPage,
    PointsSummary,
)


REGISTRATION_AMOUNT = 100
REGISTRATION_TITLE = "注册"
Kind = Literal["earn", "spend"]


def registration_event_key(user_id: uuid.UUID) -> str:
    return f"register:{user_id}"


class PointsService:
    def __init__(self, entries: PointsRepository) -> None:
        self._entries = entries

    async def grant_registration(self, user_id: uuid.UUID) -> None:
        event_key = registration_event_key(user_id)
        await self._entries.lock_user(user_id)
        if await self._entries.get_by_event_key(event_key) is not None:
            return

        balance = await self._entries.latest_balance(user_id)
        await self._entries.add_or_ignore_duplicate(
            PointsEntry(
                user_id=user_id,
                kind="earn",
                amount=REGISTRATION_AMOUNT,
                title=REGISTRATION_TITLE,
                balance_after=balance + REGISTRATION_AMOUNT,
                event_key=event_key,
            )
        )

    async def balance(self, user_id: uuid.UUID) -> int:
        return await self._entries.latest_balance(user_id)

    async def summary(self, user_id: uuid.UUID) -> PointsSummary:
        today = today_local()
        start, end = local_day_bounds(today)
        signed = await self._entries.checkin_dates(user_id)
        counts = await self._entries.earn_title_counts(user_id, DAILY_TITLES, start, end)
        return PointsSummary(
            earned=await self._entries.sum_amount(user_id, "earn"),
            spent=await self._entries.sum_amount(user_id, "spend"),
            balance=await self._entries.latest_balance(user_id),
            streak=current_streak(today, signed),
            makeup_card_count=await self._entries.makeup_card_count(user_id),
            today_checked=today in signed,
            makeup_dates=missing_makeup_dates(today, signed),
            checkin_dates=visible_checkin_dates(today, signed),
            today_post_count=counts[POST_TITLE],
            today_comment_count=counts[COMMENT_TITLE],
            today_like_count=counts[LIKE_TITLE],
        )

    async def ledger(
        self,
        user_id: uuid.UUID,
        page: PageQuery,
        kind: str | None,
        range_key: str | None,
    ) -> PointsEntryPage:
        selected_kind = normalize_kind(kind)
        selected_range = normalize_range(range_key)
        start, end = ledger_bounds(selected_range, today_local())
        rows, total = await self._entries.list_ledger(
            user_id,
            kind=selected_kind,
            start=start,
            end=end,
            offset=(page.page - 1) * page.page_size,
            limit=page.page_size,
        )
        return PointsEntryPage(
            items=[_present(row) for row in rows],
            total=total,
            page=page.page,
            page_size=page.page_size,
        )

    async def checkin(self, user_id: uuid.UUID) -> CheckinResult:
        return await perform_checkin(self._entries, user_id)

    async def makeup(self, user_id: uuid.UUID, raw_date: object) -> MakeupResult:
        return await perform_makeup(self._entries, user_id, raw_date)

    async def award_published_post(self, user_id: uuid.UUID) -> None:
        await award_published_post_for(self._entries, user_id)

    async def award_comment(self, user_id: uuid.UUID) -> None:
        await award_comment_for(self._entries, user_id)

    async def award_like(self, user_id: uuid.UUID) -> None:
        await award_like_for(self._entries, user_id)

    async def spend(self, user_id: uuid.UUID, amount: int, title: str, event_key: str) -> None:
        await spend_for(self._entries, user_id, amount, title, event_key)


def _present(row: PointsEntry) -> PointsEntryOut:
    return PointsEntryOut(
        id=str(row.id),
        kind=_kind(row.kind),
        amount=row.amount,
        title=row.title,
        balance_after=row.balance_after,
        created_at=format_utc(row.created_at),
    )


def _kind(value: str) -> Kind:
    if value == "earn":
        return "earn"
    if value == "spend":
        return "spend"
    raise AppError(ErrorCode.INTERNAL, "Internal server error", 500)
