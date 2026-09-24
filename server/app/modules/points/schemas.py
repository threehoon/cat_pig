from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class PointsSummary(BaseModel):
    earned: int
    spent: int
    balance: int
    streak: int
    makeup_card_count: int
    today_checked: bool
    makeup_dates: list[str]
    checkin_dates: list[str]
    today_post_count: int
    today_comment_count: int
    today_like_count: int


class PointsEntry(BaseModel):
    id: str
    kind: Literal["earn", "spend"]
    amount: int
    title: str
    balance_after: int
    created_at: str


class PointsEntryPage(BaseModel):
    items: list[PointsEntry]
    total: int
    page: int
    page_size: int


class CheckinResult(BaseModel):
    awarded: int
    balance: int
    already_done: bool
    date: str
    streak: int
    extra: int
    makeup_cards_awarded: int
    makeup_card_count: int


class MakeupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: Any


class MakeupResult(BaseModel):
    awarded: int
    balance: int
    date: str
    streak: int
    makeup_card_count: int
