import uuid

from app.core.clock import format_utc, today_local
from app.core.exceptions import AppError, ErrorCode
from app.core.pagination import PageQuery
from app.modules.points.service import PointsService
from app.modules.video.models import VideoTask
from app.modules.video.repository import VideoRepository
from app.modules.video.schemas import DeleteResult, Video, VideoCreate, VideoPage


POINTS_COST = 50
SPEND_TITLE = "图生视频"
RESOLUTIONS = frozenset({"540p", "720p", "1080p", "2k", "4k"})
PROMPT_MAX_CHARS = 100
IMAGE_MIN = 2
IMAGE_MAX = 9


class VideoService:
    def __init__(self, videos: VideoRepository, points: PointsService) -> None:
        self._videos = videos
        self._points = points

    async def list_videos(
        self,
        user_id: uuid.UUID,
        page: PageQuery,
        status: str | None,
    ) -> VideoPage:
        rows, total = await self._videos.list_for_user(
            user_id,
            status=status or None,
            page=page.page,
            page_size=page.page_size,
        )
        return VideoPage(
            items=[_present(row) for row in rows],
            total=total,
            page=page.page,
            page_size=page.page_size,
        )

    async def create_video(self, user_id: uuid.UUID, body: VideoCreate) -> Video:
        image_urls, prompt, resolution, title = _validated(body)
        video_id = uuid.uuid4()
        await self._points.spend(user_id, POINTS_COST, SPEND_TITLE, f"video:{video_id}")
        task = await self._videos.add(
            VideoTask(
                id=video_id,
                user_id=user_id,
                title=title,
                image_urls=image_urls,
                prompt=prompt,
                resolution=resolution,
                status="pending",
                result_url=None,
                points_cost=POINTS_COST,
                error_message=None,
            )
        )
        return _present(task)

    async def get_video(self, user_id: uuid.UUID, video_id: str) -> Video:
        task = await self._find(video_id)
        if task is None or task.user_id != user_id:
            raise AppError(ErrorCode.NOT_FOUND, "任务不存在", 404)
        return _present(task)

    async def delete_video(self, user_id: uuid.UUID, video_id: str) -> DeleteResult:
        task = await self._find(video_id)
        if task is None:
            raise AppError(ErrorCode.NOT_FOUND, "任务不存在", 404)
        if task.user_id != user_id:
            raise AppError(ErrorCode.FORBIDDEN, "只能删除自己的任务", 403)
        if task.status == "running":
            raise AppError(ErrorCode.CONFLICT, "生成中不能删除", 409)
        await self._videos.delete(task)
        return DeleteResult(ok=True)

    async def _find(self, video_id: str) -> VideoTask | None:
        parsed = _parse_uuid(video_id)
        if parsed is None:
            return None
        return await self._videos.get(parsed)


def _validated(body: VideoCreate) -> tuple[list[str], str, str, str]:
    image_urls = list(body.image_urls)
    prompt = body.prompt or ""
    if not IMAGE_MIN <= len(image_urls) <= IMAGE_MAX:
        raise AppError(ErrorCode.VALIDATION, "请选择 2–9 张照片", 400)
    if len(prompt) > PROMPT_MAX_CHARS:
        raise AppError(ErrorCode.VALIDATION, "提示词最多 100 字", 400)
    if body.resolution not in RESOLUTIONS:
        raise AppError(ErrorCode.VALIDATION, "分辨率不正确", 400)
    return image_urls, prompt, body.resolution, _title(body.title)


def _title(value: str | None) -> str:
    return (value or "").strip() or today_local().isoformat()


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


def _present(task: VideoTask) -> Video:
    return Video(
        id=str(task.id),
        title=task.title,
        image_urls=list(task.image_urls),
        prompt=task.prompt,
        resolution=task.resolution,
        status=task.status,
        result_url=task.result_url,
        points_cost=task.points_cost,
        error_message=task.error_message,
        created_at=format_utc(task.created_at),
    )
