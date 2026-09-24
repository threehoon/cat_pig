from dataclasses import dataclass

from app.modules.community.errors import validation
from app.modules.community.schemas import CommentCreate


STICKERS = frozenset({"blush", "happy", "cry", "paw", "heart", "sleep", "wow", "kiss"})
REPORT_REASONS = frozenset({"spam", "abuse", "porn", "other"})


@dataclass(frozen=True)
class NewComment:
    body: str
    sticker_ids: list[str]
    image_urls: list[str]
    audio_url: str | None
    audio_duration: int


def validate_comment(body: CommentCreate) -> NewComment:
    text = (body.body or "").strip()
    stickers = list(body.sticker_ids)
    images = list(body.image_urls)
    if len(text) > 200:
        raise validation("评论最多 200 字")
    if len(stickers) > 8:
        raise validation("贴纸最多 8 个")
    if any(item not in STICKERS for item in stickers):
        raise validation("贴纸不存在")
    if len(images) > 9:
        raise validation("图片最多 9 张")
    audio_raw = body.audio_url
    audio_url = audio_raw if isinstance(audio_raw, str) and audio_raw != "" else None
    raw_duration = body.audio_duration
    duration = 0 if raw_duration is None else raw_duration
    if duration < 0:
        duration = 0
    if audio_url is not None and (duration < 1 or duration > 60):
        raise validation("语音时长要在 1 到 60 秒")
    if audio_url is None and duration != 0:
        raise validation("没有语音文件")
    if text == "" and len(stickers) == 0 and len(images) == 0 and audio_url is None:
        raise validation("评论不能为空")
    return NewComment(
        body=text,
        sticker_ids=stickers,
        image_urls=images,
        audio_url=audio_url,
        audio_duration=duration if audio_url is not None else 0,
    )


def require_report_reason(reason: str) -> str:
    if reason not in REPORT_REASONS:
        raise validation("请选择举报原因")
    return reason
