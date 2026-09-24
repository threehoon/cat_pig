import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PageQuery
from app.modules.community.models import Follow
from app.modules.community.paging import page_scalars


def _is_unique_violation(exc: IntegrityError) -> bool:
    orig = exc.orig
    sqlstate = getattr(orig, "sqlstate", None) or getattr(orig, "pgcode", None)
    return sqlstate == "23505"


class FollowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, follower_id: uuid.UUID, followee_id: uuid.UUID) -> Follow | None:
        return await self._session.get(Follow, (follower_id, followee_id))

    async def add(self, follower_id: uuid.UUID, followee_id: uuid.UUID) -> bool:
        try:
            async with self._session.begin_nested():
                self._session.add(Follow(follower_id=follower_id, followee_id=followee_id))
                await self._session.flush()
        except IntegrityError as exc:
            if _is_unique_violation(exc):
                return False
            raise
        return True

    async def delete(self, follower_id: uuid.UUID, followee_id: uuid.UUID) -> None:
        existing = await self.get(follower_id, followee_id)
        if existing is None:
            return
        await self._session.delete(existing)
        await self._session.flush()

    async def list_followees(self, user_id: uuid.UUID, page: PageQuery) -> tuple[list[uuid.UUID], int]:
        statement = (
            select(Follow.followee_id)
            .where(Follow.follower_id == user_id)
            .order_by(Follow.created_at.desc(), Follow.followee_id.desc())
        )
        rows, total = await page_scalars(self._session, statement, page)
        return rows, total

    async def list_followers(self, user_id: uuid.UUID, page: PageQuery) -> tuple[list[uuid.UUID], int]:
        statement = (
            select(Follow.follower_id)
            .where(Follow.followee_id == user_id)
            .order_by(Follow.created_at.desc(), Follow.follower_id.desc())
        )
        rows, total = await page_scalars(self._session, statement, page)
        return rows, total

    async def counts(self, user_id: uuid.UUID) -> tuple[int, int]:
        following = await self._session.scalar(
            select(func.count()).select_from(Follow).where(Follow.follower_id == user_id)
        )
        followers = await self._session.scalar(
            select(func.count()).select_from(Follow).where(Follow.followee_id == user_id)
        )
        return int(following or 0), int(followers or 0)

    async def followed_ids(self, follower_id: uuid.UUID, user_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        if not user_ids:
            return set()
        rows = await self._session.scalars(
            select(Follow.followee_id).where(
                Follow.follower_id == follower_id,
                Follow.followee_id.in_(set(user_ids)),
            )
        )
        return set(rows.all())
