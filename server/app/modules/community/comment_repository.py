import uuid

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import now_utc
from app.core.pagination import PageQuery
from app.modules.community.models import Comment, CommentLike, CommentReport
from app.modules.community.paging import page_scalars


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, comment: Comment) -> Comment:
        self._session.add(comment)
        await self._session.flush()
        return comment

    async def get(
        self,
        post_id: uuid.UUID,
        comment_id: uuid.UUID,
        *,
        lock: bool = False,
    ) -> Comment | None:
        statement = select(Comment).where(Comment.id == comment_id, Comment.post_id == post_id)
        if lock:
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def list_for_post(self, post_id: uuid.UUID, page: PageQuery) -> tuple[list[Comment], int]:
        statement = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc(), Comment.id.asc())
        )
        rows, total = await page_scalars(self._session, statement, page)
        return rows, total

    async def reparent(self, comment_id: uuid.UUID, parent_id: uuid.UUID | None) -> None:
        await self._session.execute(
            update(Comment).where(Comment.parent_id == comment_id).values(parent_id=parent_id)
        )
        await self._session.flush()

    async def delete(self, comment: Comment) -> None:
        await self._session.delete(comment)
        await self._session.flush()

    async def count_for_post(self, post_id: uuid.UUID) -> int:
        value = await self._session.scalar(
            select(func.count()).select_from(Comment).where(Comment.post_id == post_id)
        )
        return int(value or 0)

    async def liked_ids(self, user_id: uuid.UUID, comment_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        if not comment_ids:
            return set()
        rows = await self._session.scalars(
            select(CommentLike.comment_id).where(
                CommentLike.user_id == user_id,
                CommentLike.comment_id.in_(comment_ids),
            )
        )
        return set(rows.all())

    async def toggle_like(self, user_id: uuid.UUID, comment: Comment) -> bool:
        existing = await self._session.get(CommentLike, (user_id, comment.id))
        if existing is None:
            self._session.add(CommentLike(user_id=user_id, comment_id=comment.id))
            comment.like_count += 1
            await self._session.flush()
            return True
        await self._session.delete(existing)
        comment.like_count = max(0, comment.like_count - 1)
        await self._session.flush()
        return False

    async def add_report(self, user_id: uuid.UUID, comment_id: uuid.UUID, reason: str) -> None:
        statement = (
            insert(CommentReport)
            .values(
                id=uuid.uuid4(),
                comment_id=comment_id,
                user_id=user_id,
                reason=reason,
                created_at=now_utc(),
            )
            .on_conflict_do_nothing(index_elements=["user_id", "comment_id"])
        )
        await self._session.execute(statement)
