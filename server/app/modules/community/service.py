import uuid

from app.core.exceptions import AppError, ErrorCode
from app.core.pagination import PageQuery
from app.modules.auth.service import AuthService
from app.modules.community.comment_flow import CommentOps
from app.modules.community.comment_repository import CommentRepository
from app.modules.community.errors import conflict, forbidden, not_found, validation
from app.modules.community.follow_repository import FollowRepository
from app.modules.community.models import Comment as CommentRow
from app.modules.community.models import Post as PostRow
from app.modules.community.post_repository import PostRepository
from app.modules.community.post_rules import apply_post_patch, build_post, parse_follow_target, validate_new_post
from app.modules.community.present import Presenter
from app.modules.community.schemas import (
    AuthorPage,
    Comment,
    OkResult,
    Post,
    PostCreate,
    PostPage,
    PostPatch,
    ProfileCounts,
)
from app.modules.points.service import PointsService


__all__ = ["CommunityService", "ProfileCounts"]


def _strip(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _can_view(post: PostRow, viewer_id: uuid.UUID) -> bool:
    return post.status == "published" or post.user_id == viewer_id


def _page(items, total: int, page: PageQuery, kind):
    return kind(items=items, total=total, page=page.page, page_size=page.page_size)


class CommunityService(CommentOps):
    def __init__(
        self,
        posts: PostRepository,
        comments: CommentRepository,
        follows: FollowRepository,
        auth: AuthService,
        points: PointsService,
    ) -> None:
        self._posts = posts
        self._comments = comments
        self._follows = follows
        self._auth = auth
        self._points = points
        self._view = Presenter(posts, comments, follows, auth)

    async def list_posts(
        self,
        viewer_id: uuid.UUID,
        page: PageQuery,
        *,
        tab: str,
        q: str | None,
        topic: str | None,
    ) -> PostPage:
        rows, total = await self._posts.list_public(
            viewer_id,
            tab=_strip(tab) or "recommend",
            q=_strip(q),
            topic=_strip(topic),
            page=page,
        )
        return _page(await self._view.posts(viewer_id, rows), total, page, PostPage)

    async def list_mine(self, viewer_id: uuid.UUID, page: PageQuery, status: str | None) -> PostPage:
        cleaned = _strip(status)
        rows, total = await self._posts.list_mine(viewer_id, cleaned or None, page)
        return _page(await self._view.posts(viewer_id, rows), total, page, PostPage)

    async def list_favorites(self, viewer_id: uuid.UUID, page: PageQuery) -> PostPage:
        rows, total = await self._posts.list_favorites(viewer_id, page)
        return _page(await self._view.posts(viewer_id, rows), total, page, PostPage)

    async def create_post(self, user_id: uuid.UUID, body: PostCreate) -> Post:
        spec = validate_new_post(body)
        post = build_post(user_id, spec)
        if spec.status == "pending":
            post.status = "published"
        await self._posts.add(post)
        if post.status == "published":
            await self._points.award_published_post(user_id)
        return await self._one_post(user_id, post)

    async def get_post(self, viewer_id: uuid.UUID, post_id: uuid.UUID) -> Post:
        post = await self._visible(viewer_id, post_id)
        return await self._one_post(viewer_id, post)

    async def update_post(self, user_id: uuid.UUID, post_id: uuid.UUID, patch: PostPatch) -> Post:
        post = await self._owned(user_id, post_id)
        status = apply_post_patch(post, patch)
        if status is not None:
            if status == "pending" and post.status == "draft":
                post.status = "published"
                await self._posts.flush()
                await self._points.award_published_post(user_id)
                return await self._one_post(user_id, post)
            if status != post.status:
                raise validation("不能这样改状态")
        await self._posts.flush()
        return await self._one_post(user_id, post)

    async def delete_post(self, user_id: uuid.UUID, post_id: uuid.UUID) -> OkResult:
        post = await self._owned(user_id, post_id)
        await self._posts.delete(post)
        return OkResult(ok=True)

    async def toggle_like(self, user_id: uuid.UUID, post_id: uuid.UUID) -> Post:
        post = await self._visible(user_id, post_id, lock=True)
        turned_on = await self._posts.toggle_like(user_id, post)
        if turned_on:
            await self._points.award_like(user_id)
        return await self._one_post(user_id, post)

    async def toggle_favorite(self, user_id: uuid.UUID, post_id: uuid.UUID) -> Post:
        post = await self._visible(user_id, post_id, lock=True)
        await self._posts.toggle_favorite(user_id, post)
        return await self._one_post(user_id, post)

    async def follow(self, user_id: uuid.UUID, raw_target: str) -> OkResult:
        target_id = parse_follow_target(user_id, raw_target)
        await self._require_user(target_id)
        if await self._follows.get(user_id, target_id) is not None:
            raise conflict("已经关注")
        created = await self._follows.add(user_id, target_id)
        if not created:
            raise conflict("已经关注")
        return OkResult(ok=True)

    async def list_following(self, user_id: uuid.UUID, page: PageQuery) -> AuthorPage:
        ids, total = await self._follows.list_followees(user_id, page)
        return _page(await self._view.authors(ids), total, page, AuthorPage)

    async def list_followers(self, user_id: uuid.UUID, page: PageQuery) -> AuthorPage:
        ids, total = await self._follows.list_followers(user_id, page)
        return _page(await self._view.authors(ids), total, page, AuthorPage)

    async def unfollow(self, user_id: uuid.UUID, target_id: uuid.UUID) -> OkResult:
        await self._follows.delete(user_id, target_id)
        return OkResult(ok=True)

    async def profile_counts(self, user_id: uuid.UUID) -> ProfileCounts:
        post_count, like_received_count = await self._posts.published_stats(user_id)
        following_count, follower_count = await self._follows.counts(user_id)
        return ProfileCounts(
            post_count=post_count,
            like_received_count=like_received_count,
            following_count=following_count,
            follower_count=follower_count,
        )

    async def publish_album_show(
        self,
        user_id: uuid.UUID,
        *,
        title: str,
        body: str,
        image_urls: list[str],
        topic_names: list[str],
    ) -> None:
        post = PostRow(
            user_id=user_id,
            board="show",
            title=title,
            body=body,
            image_urls=list(image_urls),
            topic_names=list(topic_names),
            status="published",
            like_count=0,
            comment_count=0,
            favorite_count=0,
        )
        await self._posts.add(post)
        await self._points.award_published_post(user_id)

    async def _visible(self, viewer_id: uuid.UUID, post_id: uuid.UUID, *, lock: bool = False) -> PostRow:
        post = await self._posts.get(post_id, lock=lock)
        if post is None or not _can_view(post, viewer_id):
            raise not_found("帖子不存在")
        return post

    async def _owned(self, user_id: uuid.UUID, post_id: uuid.UUID) -> PostRow:
        post = await self._posts.get(post_id, lock=True)
        if post is None:
            raise not_found("帖子不存在")
        if post.user_id != user_id:
            raise forbidden("只能操作自己的帖子")
        return post

    async def _one_post(self, viewer_id: uuid.UUID, post: PostRow) -> Post:
        return (await self._view.posts(viewer_id, [post]))[0]

    async def _one_comment(self, viewer_id: uuid.UUID, comment: CommentRow) -> Comment:
        return (await self._view.comments(viewer_id, [comment]))[0]

    async def _thread(
        self,
        post_id: uuid.UUID,
        parent_raw: str | None,
    ) -> tuple[uuid.UUID | None, uuid.UUID | None]:
        if parent_raw is None or parent_raw.strip() == "":
            return None, None
        try:
            parent_id = uuid.UUID(parent_raw.strip())
        except ValueError:
            raise validation("要评论的内容不存在") from None
        parent = await self._comments.get(post_id, parent_id)
        if parent is None:
            raise validation("要评论的内容不存在")
        top_id = parent.id if parent.parent_id is None else parent.parent_id
        return top_id, parent.user_id

    async def _require_user(self, user_id: uuid.UUID) -> None:
        try:
            await self._auth.get_profile(user_id)
        except AppError as exc:
            if exc.code == ErrorCode.NOT_FOUND:
                raise not_found("用户不存在") from exc
            raise
