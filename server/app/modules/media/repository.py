from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.media.models import MediaObject


class MediaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, media: MediaObject) -> None:
        self._session.add(media)
        await self._session.flush()
