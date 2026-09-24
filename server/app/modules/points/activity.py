import uuid
from datetime import UTC, date, datetime, timedelta

from app.core.clock import now_utc, today_local
from app.core.exceptions import AppError, ErrorCode
from app.modules.points.models import PointsEntry
from app.modules.points.repository import PointsRepository
from app.modules.points.rules import (
    BONUS_TITLE,
    CHECKIN_AMOUNT,
    CHECKIN_TITLE,
    COMMENT_AMOUNT,
    COMMENT_CAP,
    COMMENT_TITLE,
    LIKE_AMOUNT,
    LIKE_CAP,
    LIKE_TITLE,
    MAKEUP_TITLE,
    POST_AMOUNT,
    POST_CAP,
    POST_TITLE,
    current_streak,
    local_day_bounds,
    makeup_rejection,
    streak_bonus,
)
from app.modules.points.schemas import CheckinResult, MakeupResult


async def perform_checkin(entries: PointsRepository, user_id: uuid.UUID) -> CheckinResult:
    await entries.lock_user(user_id)
    today = today_local()
    signed = await entries.checkin_dates(user_id)
    cards = await entries.makeup_card_count(user_id)
    if today in signed:
        return _checkin_result(
            awarded=0,
            balance=await entries.latest_balance(user_id),
            already_done=True,
            day=today,
            streak=current_streak(today, signed),
            extra=0,
            cards_awarded=0,
            cards=cards,
        )

    iso = today.isoformat()
    when = await _moment(entries, user_id)
    wrote = await _earn(entries, user_id, CHECKIN_AMOUNT, CHECKIN_TITLE, f"checkin:{user_id}:{iso}", when)
    if not wrote:
        return _checkin_result(
            awarded=0,
            balance=await entries.latest_balance(user_id),
            already_done=True,
            day=today,
            streak=current_streak(today, signed),
            extra=0,
            cards_awarded=0,
            cards=cards,
        )

    await entries.add_checkin(user_id, today, "checkin")
    signed.add(today)
    streak = current_streak(today, signed)
    extra = streak_bonus(streak)
    cards_awarded = 0
    if extra:
        # Later created_at so balance_after follows the bonus, not the +10.
        bonus_wrote = await _earn(
            entries,
            user_id,
            extra,
            BONUS_TITLE,
            f"checkin-bonus:{user_id}:{iso}",
            when + timedelta(microseconds=1),
        )
        if bonus_wrote:
            cards_awarded = 1
            cards = await entries.add_makeup_cards(user_id, 1)
        else:
            extra = 0
    return _checkin_result(
        awarded=CHECKIN_AMOUNT + extra,
        balance=await entries.latest_balance(user_id),
        already_done=False,
        day=today,
        streak=streak,
        extra=extra,
        cards_awarded=cards_awarded,
        cards=cards,
    )


async def perform_makeup(entries: PointsRepository, user_id: uuid.UUID, raw_date: object) -> MakeupResult:
    await entries.lock_user(user_id)
    today = today_local()
    signed = await entries.checkin_dates(user_id)
    cards = await entries.makeup_card_count(user_id)
    message = makeup_rejection(raw_date, today, signed, cards)
    if message is not None:
        raise AppError(ErrorCode.VALIDATION, message, 400)
    if not isinstance(raw_date, str):
        raise AppError(ErrorCode.VALIDATION, "日期无效", 400)

    day = date.fromisoformat(raw_date)
    wrote = await _earn(
        entries,
        user_id,
        CHECKIN_AMOUNT,
        MAKEUP_TITLE,
        f"makeup:{user_id}:{day.isoformat()}",
        await _moment(entries, user_id),
    )
    if not wrote:
        raise AppError(ErrorCode.VALIDATION, "这一天已经签过到了", 400)
    await entries.add_checkin(user_id, day, "makeup")
    cards = await entries.add_makeup_cards(user_id, -1)
    signed.add(day)
    return MakeupResult(
        awarded=CHECKIN_AMOUNT,
        balance=await entries.latest_balance(user_id),
        date=day.isoformat(),
        streak=current_streak(today, signed),
        makeup_card_count=cards,
    )


async def award_published_post(entries: PointsRepository, user_id: uuid.UUID) -> None:
    await _award_daily(entries, user_id, POST_TITLE, POST_AMOUNT, POST_CAP, "post", indexed=True)


async def award_comment(entries: PointsRepository, user_id: uuid.UUID) -> None:
    await _award_daily(entries, user_id, COMMENT_TITLE, COMMENT_AMOUNT, COMMENT_CAP, "comment", indexed=False)


async def award_like(entries: PointsRepository, user_id: uuid.UUID) -> None:
    await _award_daily(entries, user_id, LIKE_TITLE, LIKE_AMOUNT, LIKE_CAP, "like", indexed=True)


async def spend(entries: PointsRepository, user_id: uuid.UUID, amount: int, title: str, event_key: str) -> None:
    if amount < 1:
        raise AppError(ErrorCode.VALIDATION, "积分数量无效", 400)
    await entries.lock_user(user_id)
    if await entries.get_by_event_key(event_key) is not None:
        return
    balance = await entries.latest_balance(user_id)
    if balance < amount:
        raise AppError(ErrorCode.POINTS_NOT_ENOUGH, "积分不足", 409)
    await entries.add_or_ignore_duplicate(
        PointsEntry(
            user_id=user_id,
            kind="spend",
            amount=amount,
            title=title,
            balance_after=balance - amount,
            event_key=event_key,
            created_at=await _moment(entries, user_id),
        )
    )


async def _award_daily(
    entries: PointsRepository,
    user_id: uuid.UUID,
    title: str,
    amount: int,
    cap: int,
    prefix: str,
    *,
    indexed: bool,
) -> None:
    await entries.lock_user(user_id)
    today = today_local()
    start, end = local_day_bounds(today)
    counts = await entries.earn_title_counts(user_id, (title,), start, end)
    count = counts[title]
    if count >= cap:
        return
    iso = today.isoformat()
    number = count + 1
    if indexed:
        event_key = f"{prefix}:{user_id}:{iso}:{number}"
    else:
        event_key = f"{prefix}:{user_id}:{iso}"
    await _earn(entries, user_id, amount, title, event_key, await _moment(entries, user_id))


async def _earn(
    entries: PointsRepository,
    user_id: uuid.UUID,
    amount: int,
    title: str,
    event_key: str,
    when: datetime,
) -> bool:
    balance = await entries.latest_balance(user_id)
    return await entries.add_or_ignore_duplicate(
        PointsEntry(
            user_id=user_id,
            kind="earn",
            amount=amount,
            title=title,
            balance_after=balance + amount,
            event_key=event_key,
            created_at=when,
        )
    )


async def _moment(entries: PointsRepository, user_id: uuid.UUID) -> datetime:
    latest = await entries.latest_created_at(user_id)
    moment = now_utc()
    if latest is None:
        return moment
    if latest.tzinfo is None:
        latest = latest.replace(tzinfo=UTC)
    if moment <= latest:
        return latest + timedelta(microseconds=1)
    return moment


def _checkin_result(
    *,
    awarded: int,
    balance: int,
    already_done: bool,
    day: date,
    streak: int,
    extra: int,
    cards_awarded: int,
    cards: int,
) -> CheckinResult:
    return CheckinResult(
        awarded=awarded,
        balance=balance,
        already_done=already_done,
        date=day.isoformat(),
        streak=streak,
        extra=extra,
        makeup_cards_awarded=cards_awarded,
        makeup_card_count=cards,
    )
