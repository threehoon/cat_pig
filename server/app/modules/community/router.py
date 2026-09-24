import uuid
from typing import Annotated

from fastapi import APIRouter, Query

from app.core.envelope import DataEnvelope
from app.core.pagination import PageQueryDep
from app.modules.community.deps import CommunityServiceDep, CommunityUserIdDep
from app.modules.community.schemas import (
    AuthorPage,
    Comment,
    CommentCreate,
    CommentDeleteResult,
    CommentPage,
    FollowCreate,
    OkResult,
    Post,
    PostCreate,
    PostPage,
    PostPatch,
    ReportCreate,
)

router = APIRouter()


@router.get("/post/mine")
async def list_mine(
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
    page: PageQueryDep,
    status: Annotated[str | None, Query()] = None,
) -> DataEnvelope[PostPage]:
    return DataEnvelope(data=await service.list_mine(user_id, page, status))


@router.get("/post/favorite")
async def list_favorites(
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
    page: PageQueryDep,
) -> DataEnvelope[PostPage]:
    return DataEnvelope(data=await service.list_favorites(user_id, page))


@router.get("/post")
async def list_posts(
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
    page: PageQueryDep,
    tab: Annotated[str, Query()] = "recommend",
    q: Annotated[str | None, Query()] = None,
    topic: Annotated[str | None, Query()] = None,
) -> DataEnvelope[PostPage]:
    return DataEnvelope(data=await service.list_posts(user_id, page, tab=tab, q=q, topic=topic))


@router.post("/post")
async def create_post(
    body: PostCreate,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[Post]:
    return DataEnvelope(data=await service.create_post(user_id, body))


@router.get("/post/{post_id}")
async def get_post(
    post_id: uuid.UUID,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[Post]:
    return DataEnvelope(data=await service.get_post(user_id, post_id))


@router.patch("/post/{post_id}")
async def update_post(
    post_id: uuid.UUID,
    body: PostPatch,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[Post]:
    return DataEnvelope(data=await service.update_post(user_id, post_id, body))


@router.delete("/post/{post_id}")
async def delete_post(
    post_id: uuid.UUID,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[OkResult]:
    return DataEnvelope(data=await service.delete_post(user_id, post_id))


@router.post("/post/{post_id}/like")
async def like_post(
    post_id: uuid.UUID,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[Post]:
    return DataEnvelope(data=await service.toggle_like(user_id, post_id))


@router.post("/post/{post_id}/favorite")
async def favorite_post(
    post_id: uuid.UUID,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[Post]:
    return DataEnvelope(data=await service.toggle_favorite(user_id, post_id))


@router.get("/post/{post_id}/comment")
async def list_comments(
    post_id: uuid.UUID,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
    page: PageQueryDep,
) -> DataEnvelope[CommentPage]:
    return DataEnvelope(data=await service.list_comments(user_id, post_id, page))


@router.post("/post/{post_id}/comment")
async def create_comment(
    post_id: uuid.UUID,
    body: CommentCreate,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[Comment]:
    return DataEnvelope(data=await service.create_comment(user_id, post_id, body))


@router.delete("/post/{post_id}/comment/{comment_id}")
async def delete_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[CommentDeleteResult]:
    return DataEnvelope(data=await service.delete_comment(user_id, post_id, comment_id))


@router.post("/post/{post_id}/comment/{comment_id}/like")
async def like_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[Comment]:
    return DataEnvelope(data=await service.toggle_comment_like(user_id, post_id, comment_id))


@router.post("/post/{post_id}/comment/{comment_id}/report")
async def report_comment(
    post_id: uuid.UUID,
    comment_id: uuid.UUID,
    body: ReportCreate,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[OkResult]:
    return DataEnvelope(data=await service.report_comment(user_id, post_id, comment_id, body.reason))


@router.post("/follow")
async def follow_user(
    body: FollowCreate,
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[OkResult]:
    return DataEnvelope(data=await service.follow(user_id, body.user_id or ""))


@router.get("/follow")
async def list_following(
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
    page: PageQueryDep,
) -> DataEnvelope[AuthorPage]:
    return DataEnvelope(data=await service.list_following(user_id, page))


@router.get("/follower")
async def list_followers(
    user_id: CommunityUserIdDep,
    service: CommunityServiceDep,
    page: PageQueryDep,
) -> DataEnvelope[AuthorPage]:
    return DataEnvelope(data=await service.list_followers(user_id, page))


@router.delete("/follow/{user_id}")
async def unfollow_user(
    user_id: uuid.UUID,
    viewer_id: CommunityUserIdDep,
    service: CommunityServiceDep,
) -> DataEnvelope[OkResult]:
    return DataEnvelope(data=await service.unfollow(viewer_id, user_id))
