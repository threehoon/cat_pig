from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo


APP_ZONE = ZoneInfo("Asia/Shanghai")


def now_utc() -> datetime:
    return datetime.now(UTC)


def today_local() -> date:
    return datetime.now(APP_ZONE).date()


def format_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
