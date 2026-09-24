import uuid

from app.core.exceptions import AppError, ErrorCode
from app.core.settings import get_settings
from app.modules.media.models import MediaObject
from app.modules.media.repository import MediaRepository
from app.modules.media.schemas import Media


_MISSING_FILE = "请选择文件"
_MIME_BY_SUFFIX = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mpeg",
    ".aac": "audio/mpeg",
    ".wav": "audio/mpeg",
    ".silk": "audio/mpeg",
}
_SOF_MARKERS = {0xC0, 0xC2}


class MediaService:
    def __init__(self, repository: MediaRepository) -> None:
        self._repository = repository

    async def save(self, user_id: uuid.UUID, filename: str | None, payload: bytes) -> Media:
        if not payload:
            raise AppError(ErrorCode.VALIDATION, _MISSING_FILE, 400)

        suffix = _suffix(filename)
        mime = _MIME_BY_SUFFIX.get(suffix, "application/octet-stream")
        width, height = _dimensions(suffix, payload)
        stored_name = f"{uuid.uuid4()}{suffix}"
        root = get_settings().media_root
        root.mkdir(parents=True, exist_ok=True)
        destination = root / stored_name
        await self._repository.add(
            MediaObject(
                user_id=user_id,
                stored_name=stored_name,
                mime=mime,
                width=width,
                height=height,
            )
        )
        try:
            destination.write_bytes(payload)
        except OSError:
            destination.unlink(missing_ok=True)
            raise
        return Media(url=f"/media/{stored_name}", width=width, height=height, mime=mime)


def _suffix(filename: str | None) -> str:
    if not filename:
        return ".bin"
    dot = filename.rfind(".")
    if dot < 0:
        return ".bin"
    suffix = filename[dot:].lower()
    if suffix in _MIME_BY_SUFFIX:
        return suffix
    return ".bin"


def _dimensions(suffix: str, payload: bytes) -> tuple[int, int]:
    if suffix == ".png":
        return _png_size(payload)
    if suffix in {".jpg", ".jpeg"}:
        return _jpeg_size(payload)
    if suffix == ".gif":
        return _gif_size(payload)
    return 0, 0


def _png_size(payload: bytes) -> tuple[int, int]:
    if len(payload) < 24:
        return 0, 0
    width = int.from_bytes(payload[16:20], "big")
    height = int.from_bytes(payload[20:24], "big")
    return width, height


def _gif_size(payload: bytes) -> tuple[int, int]:
    if len(payload) < 10 or payload[:6] not in {b"GIF87a", b"GIF89a"}:
        return 0, 0
    width = int.from_bytes(payload[6:8], "little")
    height = int.from_bytes(payload[8:10], "little")
    return width, height


def _jpeg_size(payload: bytes) -> tuple[int, int]:
    size = len(payload)
    if size < 4 or payload[0:2] != b"\xff\xd8":
        return 0, 0

    index = 2
    while index + 1 < size:
        if payload[index] != 0xFF:
            return 0, 0
        while index < size and payload[index] == 0xFF:
            index += 1
        if index >= size:
            return 0, 0
        marker = payload[index]
        index += 1
        if marker == 0xD9:
            return 0, 0
        if marker in {0x01, 0xD8} or 0xD0 <= marker <= 0xD7:
            continue
        if index + 1 >= size:
            return 0, 0
        segment_length = int.from_bytes(payload[index : index + 2], "big")
        if segment_length < 2 or index + segment_length > size:
            return 0, 0
        if marker in _SOF_MARKERS:
            if segment_length < 7:
                return 0, 0
            height = int.from_bytes(payload[index + 3 : index + 5], "big")
            width = int.from_bytes(payload[index + 5 : index + 7], "big")
            return width, height
        if marker == 0xDA:
            return 0, 0
        index += segment_length
    return 0, 0
