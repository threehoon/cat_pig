import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.video.models import VideoTask


class VideoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, task: VideoTask) -> VideoTask:
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def get(self, video_id: uuid.UUID) -> VideoTask | None:
        return await self._session.get(VideoTask, video_id)

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[VideoTask], int]:
        filters = [VideoTask.user_id == user_id]
        if status is not None:
            filters.append(VideoTask.status == status)
        total = await self._session.scalar(
            select(func.count()).select_from(VideoTask).where(*filters)
        )
        statement = (
            select(VideoTask)
            .where(*filters)
            .order_by(VideoTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = await self._session.scalars(statement)
        return list(rows.all()), int(total or 0)

    async def delete(self, task: VideoTask) -> None:
        await self._session.delete(task)
        await self._session.flush()
