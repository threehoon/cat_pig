import uuid
from dataclasses import dataclass

from app.modules.community.errors import not_found, validation
from app.modules.community.models import Post
from app.modules.community.schemas import PostCreate, PostPatch


BOARDS = frozenset({"qa", "show", "share", "help", "daily", "experience"})
WRITABLE_STATUSES = frozenset({"draft", "pending"})


@dataclass(frozen=True)
class NewPost:
    board: str
    title: str
    body: str
    image_urls: list[str]
    topic_names: list[str]
    status: str


def require_board(value: object) -> str:
    if not isinstance(value, str) or value not in BOARDS:
        raise validation("板块不正确")
    return value


def validate_new_post(body: PostCreate) -> NewPost:
    board = body.board if body.board else "daily"
    if board not in BOARDS:
        raise validation("板块不正确")
    status = body.status or ""
    if status not in WRITABLE_STATUSES:
        raise validation("状态只允许 draft 或 pending")
    title = body.title if isinstance(body.title, str) else ""
    text = body.body if isinstance(body.body, str) else ""
    images = list(body.image_urls)
    if not text.strip() and len(images) == 0:
        raise validation("正文和图片不能同时为空")
    if len(text) > 500:
        raise validation("正文最多 500 字")
    if len(images) > 9:
        raise validation("最多 9 张照片")
    return NewPost(
        board=board,
        title=title,
        body=text,
        image_urls=images,
        topic_names=list(body.topic_names),
        status=status,
    )


def build_post(user_id: uuid.UUID, spec: NewPost) -> Post:
    return Post(
        user_id=user_id,
        board=spec.board,
        title=spec.title,
        body=spec.body,
        image_urls=list(spec.image_urls),
        topic_names=list(spec.topic_names),
        status="draft",
        like_count=0,
        comment_count=0,
        favorite_count=0,
    )


def apply_post_patch(post: Post, patch: PostPatch) -> str | None:
    data = patch.model_dump(exclude_unset=True)
    if "board" in data:
        post.board = require_board(data["board"])
    if "title" in data:
        title = data["title"]
        if not isinstance(title, str):
            raise validation("标题不正确")
        post.title = title
    if "body" in data:
        body = data["body"]
        if not isinstance(body, str) or len(body) > 500:
            raise validation("正文最多 500 字")
        post.body = body
    if "image_urls" in data:
        images = data["image_urls"]
        if not isinstance(images, list) or len(images) > 9:
            raise validation("最多 9 张照片")
        post.image_urls = [str(item) for item in images]
    if "topic_names" in data:
        topics = data["topic_names"]
        if not isinstance(topics, list):
            raise validation("话题不正确")
        post.topic_names = [str(item) for item in topics]
    if not post.body.strip() and len(post.image_urls) == 0:
        raise validation("正文和图片不能同时为空")
    if "status" not in data or data["status"] is None:
        return None if "status" not in data else ""
    status = data["status"]
    if not isinstance(status, str):
        return ""
    return status


def parse_follow_target(user_id: uuid.UUID, raw: str) -> uuid.UUID:
    text = raw.strip()
    if text == "":
        raise validation("缺少 user_id")
    try:
        target = uuid.UUID(text)
    except ValueError:
        raise not_found("用户不存在") from None
    if target == user_id:
        raise validation("不能关注自己")
    return target
