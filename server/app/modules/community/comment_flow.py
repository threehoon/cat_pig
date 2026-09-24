import uuid

from app.core.pagination import PageQuery
from app.modules.community.comment_rules import require_report_reason, validate_comment
from app.modules.community.errors import forbidden, not_found
from app.modules.community.models import Comment as CommentRow
from app.modules.community.schemas import Comment, CommentCreate, CommentDeleteResult, CommentPage, OkResult


class CommentOps:
    async def list_comments(
        self,
        viewer_id: uuid.UUID,
        post_id: uuid.UUID,
        page: PageQuery,
    ) -> CommentPage:
        await self._visible(viewer_id, post_id)
        rows, total = await self._comments.list_for_post(post_id, page)
        items = await self._view.comments(viewer_id, rows)
        return CommentPage(items=items, total=total, page=page.page, page_size=page.page_size)

    async def create_comment(
        self,
        user_id: uuid.UUID,
        post_id: uuid.UUID,
        body: CommentCreate,
    ) -> Comment:
        post = await self._visible(user_id, post_id, lock=True)
        spec = validate_comment(body)
        parent_id, reply_to = await self._thread(post.id, body.parent_id)
        row = CommentRow(
            post_id=post.id,
            user_id=user_id,
            body=spec.body,
            parent_id=parent_id,
            reply_to_user_id=reply_to,
            sticker_ids=list(spec.sticker_ids),
            image_urls=list(spec.image_urls),
            audio_url=spec.audio_url,
            audio_duration=spec.audio_duration,
            like_count=0,
        )
        await self._comments.add(row)
        post.comment_count += 1
        await self._posts.flush()
        await self._points.award_comment(user_id)
        return await self._one_comment(user_id, row)

    async def delete_comment(
        self,
        user_id: uuid.UUID,
        post_id: uuid.UUID,
        comment_id: uuid.UUID,
    ) -> CommentDeleteResult:
        post = await self._posts.get(post_id, lock=True)
        if post is None:
            raise not_found("帖子不存在")
        comment = await self._comments.get(post_id, comment_id, lock=True)
        if comment is None:
            raise not_found("评论不存在")
        if comment.user_id != user_id and post.user_id != user_id:
            raise forbidden("只能删除自己的评论")
        await self._comments.reparent(comment.id, comment.parent_id)
        await self._comments.delete(comment)
        post.comment_count = await self._comments.count_for_post(post.id)
        await self._posts.flush()
        return CommentDeleteResult(ok=True, comment_count=post.comment_count)

    async def toggle_comment_like(
        self,
        user_id: uuid.UUID,
        post_id: uuid.UUID,
        comment_id: uuid.UUID,
    ) -> Comment:
        await self._visible(user_id, post_id)
        comment = await self._comments.get(post_id, comment_id, lock=True)
        if comment is None:
            raise not_found("评论不存在")
        await self._comments.toggle_like(user_id, comment)
        return await self._one_comment(user_id, comment)

    async def report_comment(
        self,
        user_id: uuid.UUID,
        post_id: uuid.UUID,
        comment_id: uuid.UUID,
        reason: str,
    ) -> OkResult:
        await self._visible(user_id, post_id)
        comment = await self._comments.get(post_id, comment_id)
        if comment is None:
            raise not_found("评论不存在")
        if comment.user_id == user_id:
            raise forbidden("不能举报自己的评论")
        await self._comments.add_report(user_id, comment.id, require_report_reason(reason))
        return OkResult(ok=True)
