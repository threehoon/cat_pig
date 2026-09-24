import logging
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.album.models import Album


logger = logging.getLogger(__name__)


class AlbumRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, album: Album) -> Album:
        self._session.add(album)
        await self._session.flush()
        await self._session.refresh(album)
        return album

    async def get(self, album_id: uuid.UUID) -> Album | None:
        return await self._session.get(Album, album_id)

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[Album], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(Album).where(Album.user_id == user_id)
        )
        statement = (
            select(Album)
            .where(Album.user_id == user_id)
            .order_by(Album.created_at.desc(), Album.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(await self._session.scalars(statement))
        return rows, int(total or 0)

    async def flush(self, album: Album) -> Album:
        await self._session.flush()
        await self._session.refresh(album)
        return album

    async def remove(self, album: Album) -> None:
        await self._session.delete(album)
        await self._session.flush()

    async def sync_show(self, community: object, user_id: uuid.UUID, album: Album) -> None:
        # Savepoint: community failure must not roll back the album row.
        publisher: Any = community
        try:
            async with self._session.begin_nested():
                await publisher.publish_album_show(
                    user_id,
                    title=album.title,
                    body=album.body,
                    image_urls=list(album.image_urls),
                    topic_names=list(album.tag_names),
                )
        except Exception:
            logger.warning("album forum sync failed", exc_info=True)
