import re
from datetime import date, datetime, time, timedelta

from app.core.clock import APP_ZONE
from app.core.exceptions import AppError, ErrorCode


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
POST_TITLE = "发布帖子"
COMMENT_TITLE = "评论"
LIKE_TITLE = "点赞"
CHECKIN_TITLE = "签到"
BONUS_TITLE = "连续签到奖励"
MAKEUP_TITLE = "补签"
DAILY_TITLES = (POST_TITLE, COMMENT_TITLE, LIKE_TITLE)
CHECKIN_AMOUNT = 10
POST_AMOUNT = 20
POST_CAP = 3
COMMENT_AMOUNT = 5
COMMENT_CAP = 1
LIKE_AMOUNT = 2
LIKE_CAP = 3
_KINDS = frozenset({"earn", "spend"})
_RANGES = frozenset({"all", "month", "quarter"})


def shift_month(first_of_month: date, months: int) -> date:
    index = first_of_month.month - 1 + months
    year = first_of_month.year + index // 12
    month = index % 12 + 1
    return date(year, month, 1)


def at_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=APP_ZONE)


def local_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = at_start(day)
    return start, start + timedelta(days=1)


def current_streak(today: date, signed: set[date]) -> int:
    cursor = today if today in signed else today - timedelta(days=1)
    if cursor not in signed:
        return 0
    count = 0
    while cursor in signed:
        count += 1
        cursor -= timedelta(days=1)
    return count


def streak_bonus(streak: int) -> int:
    if streak == 3:
        return 20
    if streak == 7:
        return 50
    return 0


def makeup_window(today: date) -> list[date]:
    return [today - timedelta(days=offset) for offset in range(1, 7)]


def missing_makeup_dates(today: date, signed: set[date]) -> list[str]:
    return [day.isoformat() for day in makeup_window(today) if day not in signed]


def visible_checkin_dates(today: date, signed: set[date]) -> list[str]:
    month_start = today.replace(day=1)
    start = shift_month(month_start, -1)
    end = shift_month(month_start, 1)
    return [day.isoformat() for day in sorted(signed) if start <= day < end]


def ledger_bounds(range_key: str, today: date) -> tuple[datetime | None, datetime | None]:
    if range_key == "all":
        return None, None
    month_start = today.replace(day=1)
    if range_key == "month":
        return at_start(month_start), at_start(shift_month(month_start, 1))
    return at_start(shift_month(month_start, -2)), None


def normalize_kind(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value not in _KINDS:
        raise AppError(ErrorCode.VALIDATION, "kind 无效", 400)
    return value


def normalize_range(value: str | None) -> str:
    if value is None or value == "":
        return "all"
    if value not in _RANGES:
        raise AppError(ErrorCode.VALIDATION, "range 无效", 400)
    return value


def makeup_rejection(raw: object, today: date, signed: set[date], cards: int) -> str | None:
    # Same order as the miniprogram mock: format, today, signed, card, window.
    if not isinstance(raw, str) or DATE_RE.fullmatch(raw) is None:
        return "日期无效"
    if raw == today.isoformat():
        return "不能补今天"
    parsed = _parse_date(raw)
    if parsed is not None and parsed in signed:
        return "这一天已经签过到了"
    if cards < 1:
        return "无法补签"
    if parsed not in set(makeup_window(today)):
        return "不在可补签范围内"
    return None


def _parse_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None
