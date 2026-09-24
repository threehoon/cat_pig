import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.points.models import PointsCard, PointsCheckin, PointsEntry


def _lock_key(user_id: uuid.UUID) -> int:
    return int.from_bytes(user_id.bytes[:8], "big", signed=True)


def _as_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


class PointsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def lock_user(self, user_id: uuid.UUID) -> None:
        await self._session.execute(
            text("SELECT pg_advisory_xact_lock(CAST(:key AS bigint))"),
            {"key": _lock_key(user_id)},
        )

    async def get_by_event_key(self, event_key: str) -> PointsEntry | None:
        return await self._session.scalar(select(PointsEntry).where(PointsEntry.event_key == event_key))

    async def latest_balance(self, user_id: uuid.UUID) -> int:
        statement = (
            select(PointsEntry.balance_after)
            .where(PointsEntry.user_id == user_id)
            .order_by(PointsEntry.created_at.desc(), PointsEntry.id.desc())
            .limit(1)
        )
        balance = await self._session.scalar(statement)
        if balance is None:
            return 0
        return balance

    async def latest_created_at(self, user_id: uuid.UUID) -> datetime | None:
        statement = select(func.max(PointsEntry.created_at)).where(PointsEntry.user_id == user_id)
        return await self._session.scalar(statement)

    async def add_or_ignore_duplicate(self, entry: PointsEntry) -> bool:
        try:
            async with self._session.begin_nested():
                self._session.add(entry)
                await self._session.flush()
        except IntegrityError:
            return False
        return True

    async def sum_amount(self, user_id: uuid.UUID, kind: str) -> int:
        statement = select(func.sum(PointsEntry.amount)).where(
            PointsEntry.user_id == user_id,
            PointsEntry.kind == kind,
        )
        return _as_int(await self._session.scalar(statement))

    async def earn_title_counts(
        self,
        user_id: uuid.UUID,
        titles: tuple[str, ...],
        start: datetime,
        end: datetime,
    ) -> dict[str, int]:
        counts = {title: 0 for title in titles}
        if not titles:
            return counts
        statement = (
            select(PointsEntry.title, func.count())
            .where(
                PointsEntry.user_id == user_id,
                PointsEntry.kind == "earn",
                PointsEntry.title.in_(titles),
                PointsEntry.created_at >= start,
                PointsEntry.created_at < end,
            )
            .group_by(PointsEntry.title)
        )
        rows = await self._session.execute(statement)
        for title, count in rows.all():
            counts[str(title)] = _as_int(count)
        return counts

    async def list_ledger(
        self,
        user_id: uuid.UUID,
        *,
        kind: str | None,
        start: datetime | None,
        end: datetime | None,
        offset: int,
        limit: int,
    ) -> tuple[list[PointsEntry], int]:
        conditions = [PointsEntry.user_id == user_id]
        if kind is not None:
            conditions.append(PointsEntry.kind == kind)
        if start is not None:
            conditions.append(PointsEntry.created_at >= start)
        if end is not None:
            conditions.append(PointsEntry.created_at < end)
        total = await self._session.scalar(
            select(func.count()).select_from(PointsEntry).where(*conditions)
        )
        rows = await self._session.scalars(
            select(PointsEntry)
            .where(*conditions)
            .order_by(PointsEntry.created_at.desc(), PointsEntry.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(rows.all()), _as_int(total)

    async def checkin_dates(self, user_id: uuid.UUID) -> set[date]:
        rows = await self._session.scalars(
            select(PointsCheckin.local_date).where(PointsCheckin.user_id == user_id)
        )
        return set(rows.all())

    async def add_checkin(self, user_id: uuid.UUID, local_date: date, source: str) -> None:
        self._session.add(PointsCheckin(user_id=user_id, local_date=local_date, source=source))
        await self._session.flush()

    async def makeup_card_count(self, user_id: uuid.UUID) -> int:
        row = await self._session.get(PointsCard, user_id)
        if row is None:
            return 0
        return row.makeup_card_count

    async def add_makeup_cards(self, user_id: uuid.UUID, count: int) -> int:
        row = await self._session.get(PointsCard, user_id)
        if row is None:
            row = PointsCard(user_id=user_id, makeup_card_count=0)
            self._session.add(row)
        row.makeup_card_count += count
        await self._session.flush()
        return row.makeup_card_count
