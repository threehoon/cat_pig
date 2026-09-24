import json
import uuid

from sqlalchemy import bindparam, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import PageQuery
from app.modules.community.models import Follow, Post, PostFavorite, PostLike
from app.modules.community.paging import page_scalars
from app.modules.community.post_rules import BOARDS


def _like_pattern(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _topic_exact(topic: str):
    payload = json.dumps([topic], ensure_ascii=False)
    return text("post.topic_names @> CAST(:topic_exact AS jsonb)").bindparams(
        bindparam("topic_exact", payload)
    )


def _topic_substring(pattern: str):
    return text(
        "EXISTS (SELECT 1 FROM jsonb_array_elements_text(post.topic_names) AS topic_name(value) "
        "WHERE topic_name.value LIKE :topic_like_pattern ESCAPE '\\')"
    ).bindparams(bindparam("topic_like_pattern", pattern))


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, post: Post) -> Post:
        self._session.add(post)
        await self._session.flush()
        return post

    async def flush(self) -> None:
        await self._session.flush()

    async def get(self, post_id: uuid.UUID, *, lock: bool = False) -> Post | None:
        statement = select(Post).where(Post.id == post_id)
        if lock:
            statement = statement.with_for_update()
        return await self._session.scalar(statement)

    async def delete(self, post: Post) -> None:
        await self._session.delete(post)
        await self._session.flush()

    async def list_public(
        self,
        viewer_id: uuid.UUID,
        *,
        tab: str,
        q: str,
        topic: str,
        page: PageQuery,
    ) -> tuple[list[Post], int]:
        statement = select(Post).where(Post.status == "published")
        if tab == "following":
            followed = select(Follow.followee_id).where(Follow.follower_id == viewer_id)
            statement = statement.where(Post.user_id.in_(followed))
        elif tab in BOARDS:
            statement = statement.where(Post.board == tab)
        if topic:
            statement = statement.where(_topic_exact(topic))
        if q:
            pattern = _like_pattern(q)
            statement = statement.where(
                or_(
                    Post.title.like(pattern, escape="\\"),
                    Post.body.like(pattern, escape="\\"),
                    _topic_substring(pattern),
                )
            )
        statement = statement.order_by(Post.created_at.desc(), Post.id.desc())
        rows, total = await page_scalars(self._session, statement, page)
        return rows, total

    async def list_mine(
        self,
        user_id: uuid.UUID,
        status: str | None,
        page: PageQuery,
    ) -> tuple[list[Post], int]:
        statement = select(Post).where(Post.user_id == user_id)
        if status:
            statement = statement.where(Post.status == status)
        statement = statement.order_by(Post.created_at.desc(), Post.id.desc())
        rows, total = await page_scalars(self._session, statement, page)
        return rows, total

    async def list_favorites(self, user_id: uuid.UUID, page: PageQuery) -> tuple[list[Post], int]:
        statement = (
            select(Post)
            .join(PostFavorite, PostFavorite.post_id == Post.id)
            .where(PostFavorite.user_id == user_id)
            .order_by(Post.created_at.desc(), Post.id.desc())
        )
        rows, total = await page_scalars(self._session, statement, page)
        return rows, total

    async def liked_ids(self, user_id: uuid.UUID, post_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        if not post_ids:
            return set()
        rows = await self._session.scalars(
            select(PostLike.post_id).where(
                PostLike.user_id == user_id,
                PostLike.post_id.in_(post_ids),
            )
        )
        return set(rows.all())

    async def favorited_ids(self, user_id: uuid.UUID, post_ids: list[uuid.UUID]) -> set[uuid.UUID]:
        if not post_ids:
            return set()
        rows = await self._session.scalars(
            select(PostFavorite.post_id).where(
                PostFavorite.user_id == user_id,
                PostFavorite.post_id.in_(post_ids),
            )
        )
        return set(rows.all())

    async def toggle_like(self, user_id: uuid.UUID, post: Post) -> bool:
        existing = await self._session.get(PostLike, (user_id, post.id))
        if existing is None:
            self._session.add(PostLike(user_id=user_id, post_id=post.id))
            post.like_count += 1
            await self._session.flush()
            return True
        await self._session.delete(existing)
        post.like_count = max(0, post.like_count - 1)
        await self._session.flush()
        return False

    async def toggle_favorite(self, user_id: uuid.UUID, post: Post) -> bool:
        existing = await self._session.get(PostFavorite, (user_id, post.id))
        if existing is None:
            self._session.add(PostFavorite(user_id=user_id, post_id=post.id))
            post.favorite_count += 1
            await self._session.flush()
            return True
        await self._session.delete(existing)
        post.favorite_count = max(0, post.favorite_count - 1)
        await self._session.flush()
        return False

    async def published_stats(self, user_id: uuid.UUID) -> tuple[int, int]:
        row = await self._session.execute(
            select(
                func.count(Post.id),
                func.coalesce(func.sum(Post.like_count), 0),
            ).where(Post.user_id == user_id, Post.status == "published")
        )
        count, likes = row.one()
        return int(count), int(likes)
