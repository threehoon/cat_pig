from email import message_from_bytes
from email.message import Message
from email.policy import HTTP

from fastapi import APIRouter, Request

from app.core.envelope import DataEnvelope
from app.modules.media.deps import MediaServiceDep, MediaUserIdDep
from app.modules.media.schemas import Media


router = APIRouter()


@router.post("")
async def create_media(
    request: Request,
    user_id: MediaUserIdDep,
    service: MediaServiceDep,
) -> DataEnvelope[Media]:
    filename, payload = _multipart_file(
        request.headers.get("content-type", ""),
        await request.body(),
    )
    return DataEnvelope(data=await service.save(user_id, filename, payload))


def _multipart_file(content_type: str, body: bytes) -> tuple[str | None, bytes]:
    # python-multipart is not installed; read the file part with the stdlib.
    if not content_type or "\r" in content_type or "\n" in content_type:
        return None, b""
    if "multipart/form-data" not in content_type.lower():
        return None, b""
    try:
        encoded_type = content_type.encode("latin-1")
    except UnicodeEncodeError:
        return None, b""

    raw = b"Content-Type: " + encoded_type + b"\r\nMIME-Version: 1.0\r\n\r\n" + body
    message = message_from_bytes(raw, policy=HTTP)
    if not message.is_multipart():
        return None, b""
    for part in message.iter_parts():
        if not isinstance(part, Message) or _part_name(part) != "file":
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            return None, b""
        filename = part.get_filename()
        return None if filename is None else str(filename), payload
    return None, b""


def _part_name(part: Message) -> str | None:
    value = part.get_param("name", header="content-disposition")
    if not isinstance(value, str):
        return None
    return value
