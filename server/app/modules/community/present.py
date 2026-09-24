import uuid
from typing import cast

from app.core.clock import format_utc
from app.modules.auth.schemas import UserProfile
from app.modules.auth.service import AuthService
from app.modules.community.comment_repository import CommentRepository
from app.modules.community.follow_repository import FollowRepository
from app.modules.community.models import Comment as CommentRow
from app.modules.community.models import Post as PostRow
from app.modules.community.post_repository import PostRepository
from app.modules.community.schemas import Author, Board, Comment, Post, PostStatus


def author_from(profile: UserProfile) -> Author:
    return Author(id=profile.id, nickname=profile.nickname, avatar_url=profile.avatar_url)


def post_from(
    row: PostRow,
    profile: UserProfile,
    *,
    followed: bool,
    liked: bool,
    favorited: bool,
) -> Post:
    return Post(
        id=str(row.id),
        author=author_from(profile),
        board=cast(Board, row.board),
        title=row.title,
        body=row.body,
        image_urls=list(row.image_urls or []),
        topic_names=list(row.topic_names or []),
        status=cast(PostStatus, row.status),
        followed=followed,
        like_count=row.like_count,
        comment_count=row.comment_count,
        favorite_count=row.favorite_count,
        liked=liked,
        favorited=favorited,
        created_at=format_utc(row.created_at),
    )


def comment_from(
    row: CommentRow,
    profiles: dict[uuid.UUID, UserProfile],
    *,
    liked: bool,
) -> Comment:
    reply = None
    if row.reply_to_user_id is not None:
        reply = author_from(profiles[row.reply_to_user_id])
    return Comment(
        id=str(row.id),
        author=author_from(profiles[row.user_id]),
        body=row.body,
        parent_id=None if row.parent_id is None else str(row.parent_id),
        reply_to=reply,
        sticker_ids=list(row.sticker_ids or []),
        image_urls=list(row.image_urls or []),
        audio_url=row.audio_url,
        audio_duration=row.audio_duration,
        like_count=row.like_count,
        liked=liked,
        created_at=format_utc(row.created_at),
    )


class Presenter:
    def __init__(
        self,
        posts: PostRepository,
        comments: CommentRepository,
        follows: FollowRepository,
        auth: AuthService,
    ) -> None:
        self._posts = posts
        self._comments = comments
        self._follows = follows
        self._auth = auth

    async def profiles(self, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, UserProfile]:
        found: dict[uuid.UUID, UserProfile] = {}
        for user_id in user_ids:
            if user_id not in found:
                found[user_id] = await self._auth.get_profile(user_id)
        return found

    async def posts(self, viewer_id: uuid.UUID, rows: list[PostRow]) -> list[Post]:
        if not rows:
            return []
        profiles = await self.profiles([row.user_id for row in rows])
        post_ids = [row.id for row in rows]
        liked = await self._posts.liked_ids(viewer_id, post_ids)
        favorited = await self._posts.favorited_ids(viewer_id, post_ids)
        followed = await self._follows.followed_ids(viewer_id, [row.user_id for row in rows])
        return [
            post_from(
                row,
                profiles[row.user_id],
                followed=row.user_id in followed,
                liked=row.id in liked,
                favorited=row.id in favorited,
            )
            for row in rows
        ]

    async def comments(self, viewer_id: uuid.UUID, rows: list[CommentRow]) -> list[Comment]:
        if not rows:
            return []
        user_ids: list[uuid.UUID] = []
        for row in rows:
            user_ids.append(row.user_id)
            if row.reply_to_user_id is not None:
                user_ids.append(row.reply_to_user_id)
        profiles = await self.profiles(user_ids)
        liked = await self._comments.liked_ids(viewer_id, [row.id for row in rows])
        return [comment_from(row, profiles, liked=row.id in liked) for row in rows]

    async def authors(self, user_ids: list[uuid.UUID]) -> list[Author]:
        profiles = await self.profiles(user_ids)
        return [author_from(profiles[user_id]) for user_id in user_ids]
