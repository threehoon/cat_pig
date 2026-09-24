import uuid

from app.core.clock import format_utc
from app.core.exceptions import AppError, ErrorCode
from app.core.pagination import PageQuery
from app.modules.album.models import Album as AlbumRow
from app.modules.album.repository import AlbumRepository
from app.modules.album.schemas import Album, AlbumDeleted, AlbumPage, AlbumWrite, Visibility


_VISIBILITIES = frozenset({"public", "private", "friends"})
_PHOTO_COUNT = "照片数量须为 1\u20139 张"


class AlbumService:
    def __init__(self, albums: AlbumRepository, community: object) -> None:
        self._albums = albums
        self._community = community

    async def list_albums(self, user_id: uuid.UUID, page: PageQuery) -> AlbumPage:
        rows, total = await self._albums.list_for_user(user_id, page.page, page.page_size)
        return AlbumPage(
            items=[_present(row) for row in rows],
            total=total,
            page=page.page,
            page_size=page.page_size,
        )

    async def create_album(self, user_id: uuid.UUID, payload: AlbumWrite) -> Album:
        title = _trimmed(payload.title)
        body = _trimmed(payload.body)
        if not title or not body:
            raise _invalid("标题和说明不能为空")
        image_urls = list(payload.image_urls or [])
        _require_create_images(image_urls)
        visibility = _visibility(payload.visibility, "private")
        sync_to_forum = payload.sync_to_forum is True
        _require_public_sync(visibility, sync_to_forum)
        cover_url = _cover(payload.cover_url, image_urls)
        tag_names = list(payload.tag_names or [])
        saved = await self._albums.add(
            AlbumRow(
                user_id=user_id,
                title=title,
                body=body,
                image_urls=image_urls,
                cover_url=cover_url,
                tag_names=tag_names,
                visibility=visibility,
                sync_to_forum=sync_to_forum,
            )
        )
        presented = _present(saved)
        if saved.sync_to_forum:
            await self._albums.sync_show(self._community, user_id, saved)
        return presented

    async def get_album(self, user_id: uuid.UUID, album_id: str) -> Album:
        row = await self._load(album_id)
        if row is None or row.user_id != user_id:
            raise AppError(ErrorCode.NOT_FOUND, "相册不存在", 404)
        return _present(row)

    async def patch_album(self, user_id: uuid.UUID, album_id: str, payload: AlbumWrite) -> Album:
        row = await self._owned(user_id, album_id, "只能修改自己的相册")
        next_visibility = _visibility(payload.visibility, row.visibility)
        next_sync = _patched_sync(payload, row.sync_to_forum)
        was_synced = row.sync_to_forum
        if row.visibility == "public" and was_synced and next_visibility != "public":
            raise _invalid("已同步的公开相册不能改为非公开")
        _require_public_sync(next_visibility, next_sync)
        title = _patched_text(payload, "title")
        if title is not None and not title:
            raise _invalid("标题不能为空")
        body = _patched_text(payload, "body")
        if body is not None and not body:
            raise _invalid("说明不能为空")
        image_urls = _patched_list(payload, "image_urls")
        if image_urls is not None:
            _require_patch_images(image_urls)
        tag_names = _patched_list(payload, "tag_names")
        if title is not None:
            row.title = title
        if body is not None:
            row.body = body
        if image_urls is not None:
            row.image_urls = image_urls
            row.cover_url = image_urls[0]
        cover_url = _explicit_cover(payload)
        if cover_url is not None:
            row.cover_url = cover_url
        if tag_names is not None:
            row.tag_names = tag_names
        row.visibility = next_visibility
        row.sync_to_forum = next_sync
        saved = await self._albums.flush(row)
        presented = _present(saved)
        if next_sync and not was_synced:
            await self._albums.sync_show(self._community, user_id, saved)
        return presented

    async def delete_album(self, user_id: uuid.UUID, album_id: str) -> AlbumDeleted:
        row = await self._owned(user_id, album_id, "只能删除自己的相册")
        await self._albums.remove(row)
        return AlbumDeleted(ok=True)

    async def _load(self, album_id: str) -> AlbumRow | None:
        try:
            parsed = uuid.UUID(album_id)
        except ValueError:
            return None
        return await self._albums.get(parsed)

    async def _owned(self, user_id: uuid.UUID, album_id: str, forbidden: str) -> AlbumRow:
        row = await self._load(album_id)
        if row is None:
            raise AppError(ErrorCode.NOT_FOUND, "相册不存在", 404)
        if row.user_id != user_id:
            raise AppError(ErrorCode.FORBIDDEN, forbidden, 403)
        return row


def _invalid(message: str) -> AppError:
    return AppError(ErrorCode.VALIDATION, message, 400)


def _trimmed(value: str | None) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _visibility(value: str | None, fallback: str) -> str:
    if value is None or value == "":
        return fallback
    if value not in _VISIBILITIES:
        raise _invalid("可见性不正确")
    return value


def _require_public_sync(visibility: str, sync_to_forum: bool) -> None:
    if sync_to_forum and visibility != "public":
        raise _invalid("只有公开相册可以同步到广场")


def _require_create_images(image_urls: list[str]) -> None:
    if len(image_urls) < 1:
        raise _invalid("至少上传一张照片")
    if len(image_urls) > 9:
        raise _invalid("最多 9 张照片")


def _require_patch_images(image_urls: list[str]) -> None:
    if len(image_urls) < 1 or len(image_urls) > 9:
        raise _invalid(_PHOTO_COUNT)


def _cover(value: str | None, image_urls: list[str]) -> str:
    if isinstance(value, str) and value:
        return value
    return image_urls[0]


def _explicit_cover(payload: AlbumWrite) -> str | None:
    if "cover_url" not in payload.model_fields_set:
        return None
    if isinstance(payload.cover_url, str) and payload.cover_url:
        return payload.cover_url
    return None


def _patched_text(payload: AlbumWrite, field: str) -> str | None:
    if field not in payload.model_fields_set:
        return None
    value = getattr(payload, field)
    if not isinstance(value, str):
        return None
    return value.strip()


def _patched_list(payload: AlbumWrite, field: str) -> list[str] | None:
    if field not in payload.model_fields_set:
        return None
    value = getattr(payload, field)
    if not isinstance(value, list):
        return None
    return list(value)


def _patched_sync(payload: AlbumWrite, current: bool) -> bool:
    if "sync_to_forum" not in payload.model_fields_set:
        return current
    if not isinstance(payload.sync_to_forum, bool):
        return current
    return payload.sync_to_forum


def _response_visibility(value: str) -> Visibility:
    if value == "public" or value == "private" or value == "friends":
        return value
    raise AppError(ErrorCode.INTERNAL, "相册可见性无效", 500)


def _present(row: AlbumRow) -> Album:
    return Album(
        id=str(row.id),
        title=row.title,
        body=row.body,
        image_urls=list(row.image_urls),
        cover_url=row.cover_url,
        tag_names=list(row.tag_names),
        visibility=_response_visibility(row.visibility),
        sync_to_forum=row.sync_to_forum,
        created_at=format_utc(row.created_at),
    )
