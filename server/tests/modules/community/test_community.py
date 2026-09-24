import re
import uuid
from contextlib import asynccontextmanager

from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.core.db import SessionFactory
from app.core.security import decode_access_token
from app.main import create_app
from app.modules.auth.deps import get_auth_service, get_user_repository
from app.modules.community.deps import get_community_service
from app.modules.community.models import CommentReport
from app.modules.community.router import router
from app.modules.points.deps import get_points_repository, get_points_service


POST_FIELDS = {
    "id",
    "author",
    "board",
    "title",
    "body",
    "image_urls",
    "topic_names",
    "status",
    "followed",
    "like_count",
    "comment_count",
    "favorite_count",
    "liked",
    "favorited",
    "created_at",
}
AUTHOR_FIELDS = {"id", "nickname", "avatar_url"}
COMMENT_FIELDS = {
    "id",
    "author",
    "body",
    "parent_id",
    "reply_to",
    "sticker_ids",
    "image_urls",
    "audio_url",
    "audio_duration",
    "like_count",
    "liked",
    "created_at",
}
CREATED_AT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


def api() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test")


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def user_id_of(token: str) -> uuid.UUID:
    return uuid.UUID(decode_access_token(token))


async def login(client: AsyncClient, code: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"code": code})
    assert response.status_code == 200, response.text
    return response.json()["data"]["token"]


async def balance(client: AsyncClient, token: str) -> int:
    response = await client.get("/api/v1/me", headers=bearer(token))
    assert response.status_code == 200, response.text
    return response.json()["data"]["points_balance"]


async def create_post(client: AsyncClient, token: str, **overrides) -> dict:
    payload = {
        "title": "标题",
        "body": "正文",
        "image_urls": [],
        "topic_names": [],
        "status": "pending",
    }
    payload.update(overrides)
    response = await client.post("/api/v1/community/post", headers=bearer(token), json=payload)
    return response


def assert_error(response, status: int, code: str, message: str) -> None:
    assert response.status_code == status, response.text
    body = response.json()
    assert set(body) == {"error"}
    assert body["error"]["code"] == code
    assert body["error"]["message"] == message


def assert_post(payload: dict) -> None:
    assert set(payload) == POST_FIELDS
    assert set(payload["author"]) == AUTHOR_FIELDS
    assert CREATED_AT.fullmatch(payload["created_at"])
    assert isinstance(payload["like_count"], int)
    assert isinstance(payload["comment_count"], int)
    assert isinstance(payload["favorite_count"], int)


def assert_comment(payload: dict) -> None:
    assert set(payload) == COMMENT_FIELDS
    assert set(payload["author"]) == AUTHOR_FIELDS
    assert payload["reply_to"] is None or set(payload["reply_to"]) == AUTHOR_FIELDS
    assert CREATED_AT.fullmatch(payload["created_at"])


@asynccontextmanager
async def opened_service():
    async with SessionFactory() as session:
        points = get_points_service(get_points_repository(session))
        auth = get_auth_service(get_user_repository(session), points)
        service = get_community_service(session, auth, points)
        yield service, session


def test_static_post_routes_are_registered_before_post_id() -> None:
    paths = [route.path for route in router.routes]
    detail = paths.index("/post/{post_id}")
    assert paths.index("/post/mine") < detail
    assert paths.index("/post/favorite") < detail


async def test_post_requires_a_token() -> None:
    async with api() as client:
        response = await client.get("/api/v1/community/post")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_pending_post_publishes_and_fourth_does_not_award() -> None:
    topic = f"cap-{uuid.uuid4().hex}"
    async with api() as client:
        token = await login(client, f"community-cap-{uuid.uuid4().hex}")
        headers = bearer(token)
        assert await balance(client, token) == 100

        rejected = await create_post(client, token, status="published", topic_names=[topic])
        assert_error(rejected, 400, "VALIDATION", "状态只允许 draft 或 pending")
        empty = await create_post(client, token, body="   ", image_urls=[], topic_names=[topic])
        assert_error(empty, 400, "VALIDATION", "正文和图片不能同时为空")
        too_many = await create_post(
            client,
            token,
            image_urls=[f"https://example.com/{index}.jpg" for index in range(10)],
            topic_names=[topic],
        )
        assert_error(too_many, 400, "VALIDATION", "最多 9 张照片")
        bad_board = await create_post(client, token, board="nope", topic_names=[topic])
        assert_error(bad_board, 400, "VALIDATION", "板块不正确")
        assert await balance(client, token) == 100

        first = await create_post(client, token, title="第一帖", topic_names=[topic])
        assert first.status_code == 200, first.text
        payload = first.json()["data"]
        assert_post(payload)
        assert payload["status"] == "published"
        assert payload["board"] == "daily"
        assert payload["author"]["nickname"] is None
        assert payload["liked"] is False
        assert payload["favorited"] is False
        assert payload["followed"] is False
        assert await balance(client, token) == 120

        renamed = await client.patch(
            "/api/v1/me",
            headers=headers,
            json={"nickname": "小满", "avatar_url": "https://example.com/a.jpg"},
        )
        assert renamed.status_code == 200, renamed.text
        loaded = await client.get(f"/api/v1/community/post/{payload['id']}", headers=headers)
        assert loaded.status_code == 200, loaded.text
        assert loaded.json()["data"]["author"]["nickname"] == "小满"
        assert loaded.json()["data"]["author"]["avatar_url"] == "https://example.com/a.jpg"

        for index in range(2):
            response = await create_post(client, token, title=f"第{index + 2}帖", topic_names=[topic])
            assert response.status_code == 200, response.text
            assert response.json()["data"]["status"] == "published"
        assert await balance(client, token) == 160

        fourth = await create_post(client, token, title="第四帖", topic_names=[topic])
        assert fourth.status_code == 200, fourth.text
        assert fourth.json()["data"]["status"] == "published"
        assert await balance(client, token) == 160

        listed = await client.get(
            "/api/v1/community/post",
            headers=headers,
            params={"topic": topic, "page_size": 20},
        )
        assert listed.status_code == 200, listed.text
        body = listed.json()["data"]
        assert set(body) == {"items", "total", "page", "page_size"}
        assert body["total"] == 4
        assert [item["status"] for item in body["items"]] == ["published"] * 4
        mine_pending = await client.get(
            "/api/v1/community/post/mine",
            headers=headers,
            params={"status": "pending"},
        )
        assert mine_pending.json()["data"]["total"] == 0


async def test_draft_stays_private_and_only_author_deletes() -> None:
    title = f"草稿-{uuid.uuid4().hex}"
    async with api() as client:
        owner = await login(client, f"community-draft-a-{uuid.uuid4().hex}")
        other = await login(client, f"community-draft-b-{uuid.uuid4().hex}")
        created = await create_post(client, owner, title=title, body="还没发", status="draft")
        assert created.status_code == 200, created.text
        post = created.json()["data"]
        assert post["status"] == "draft"
        assert await balance(client, owner) == 100
        post_id = post["id"]

        public = await client.get(
            "/api/v1/community/post",
            headers=bearer(other),
            params={"q": title},
        )
        assert public.json()["data"]["total"] == 0
        mine = await client.get("/api/v1/community/post/mine", headers=bearer(owner))
        assert mine.status_code == 200, mine.text
        assert [item["id"] for item in mine.json()["data"]["items"]] == [post_id]
        hidden = await client.get(f"/api/v1/community/post/{post_id}", headers=bearer(other))
        assert_error(hidden, 404, "NOT_FOUND", "帖子不存在")
        denied = await client.delete(f"/api/v1/community/post/{post_id}", headers=bearer(other))
        assert_error(denied, 403, "FORBIDDEN", "只能操作自己的帖子")

        published = await client.patch(
            f"/api/v1/community/post/{post_id}",
            headers=bearer(owner),
            json={"status": "pending", "title": "发出去了"},
        )
        assert published.status_code == 200, published.text
        assert published.json()["data"]["status"] == "published"
        assert published.json()["data"]["title"] == "发出去了"
        assert await balance(client, owner) == 120
        visible = await client.get(f"/api/v1/community/post/{post_id}", headers=bearer(other))
        assert visible.status_code == 200, visible.text

        again = await client.patch(
            f"/api/v1/community/post/{post_id}",
            headers=bearer(owner),
            json={"status": "published"},
        )
        assert again.status_code == 200, again.text
        assert await balance(client, owner) == 120
        rewind = await client.patch(
            f"/api/v1/community/post/{post_id}",
            headers=bearer(owner),
            json={"status": "pending"},
        )
        assert_error(rewind, 400, "VALIDATION", "不能这样改状态")
        assert await balance(client, owner) == 120
        still_denied = await client.delete(f"/api/v1/community/post/{post_id}", headers=bearer(other))
        assert_error(still_denied, 403, "FORBIDDEN", "只能操作自己的帖子")
        removed = await client.delete(f"/api/v1/community/post/{post_id}", headers=bearer(owner))
        assert removed.status_code == 200, removed.text
        assert removed.json()["data"] == {"ok": True}
        gone = await client.get(f"/api/v1/community/post/{post_id}", headers=bearer(owner))
        assert_error(gone, 404, "NOT_FOUND", "帖子不存在")


async def test_like_toggle_does_not_refund() -> None:
    async with api() as client:
        token = await login(client, f"community-like-{uuid.uuid4().hex}")
        headers = bearer(token)
        created = await create_post(client, token, title="点赞帖")
        assert created.status_code == 200, created.text
        post_id = created.json()["data"]["id"]
        assert await balance(client, token) == 120

        liked = await client.post(f"/api/v1/community/post/{post_id}/like", headers=headers, json={})
        assert liked.status_code == 200, liked.text
        assert liked.json()["data"]["liked"] is True
        assert liked.json()["data"]["like_count"] == 1
        assert await balance(client, token) == 122

        unliked = await client.post(f"/api/v1/community/post/{post_id}/like", headers=headers, json={})
        assert unliked.status_code == 200, unliked.text
        assert unliked.json()["data"]["liked"] is False
        assert unliked.json()["data"]["like_count"] == 0
        assert await balance(client, token) == 122


async def test_comment_awards_once_flattens_and_reparents() -> None:
    async with api() as client:
        owner_token = await login(client, f"community-comment-a-{uuid.uuid4().hex}")
        other_token = await login(client, f"community-comment-b-{uuid.uuid4().hex}")
        owner = bearer(owner_token)
        other = bearer(other_token)
        created = await create_post(client, owner_token, title="评论帖")
        assert created.status_code == 200, created.text
        post_id = created.json()["data"]["id"]
        comment_url = f"/api/v1/community/post/{post_id}/comment"

        empty = await client.post(comment_url, headers=owner, json={"body": "   "})
        assert_error(empty, 400, "VALIDATION", "评论不能为空")
        bad_sticker = await client.post(
            comment_url,
            headers=owner,
            json={"body": "", "sticker_ids": ["nope"]},
        )
        assert_error(bad_sticker, 400, "VALIDATION", "贴纸不存在")
        missing_audio = await client.post(
            comment_url,
            headers=owner,
            json={"audio_url": "https://example.com/a.mp3", "audio_duration": 0},
        )
        assert_error(missing_audio, 400, "VALIDATION", "语音时长要在 1 到 60 秒")
        duration_only = await client.post(comment_url, headers=owner, json={"audio_duration": 5})
        assert_error(duration_only, 400, "VALIDATION", "没有语音文件")
        missing_parent = await client.post(
            comment_url,
            headers=owner,
            json={"body": "找不到", "parent_id": str(uuid.uuid4())},
        )
        assert_error(missing_parent, 400, "VALIDATION", "要评论的内容不存在")
        assert await balance(client, owner_token) == 120

        top = await client.post(comment_url, headers=owner, json={"body": "顶层"})
        assert top.status_code == 200, top.text
        top_body = top.json()["data"]
        assert_comment(top_body)
        assert top_body["parent_id"] is None
        assert top_body["reply_to"] is None
        assert await balance(client, owner_token) == 125

        voice = await client.post(
            comment_url,
            headers=owner,
            json={"audio_url": "https://example.com/a.mp3", "audio_duration": 12, "sticker_ids": ["paw"]},
        )
        assert voice.status_code == 200, voice.text
        voice_body = voice.json()["data"]
        assert voice_body["body"] == ""
        assert voice_body["audio_url"] == "https://example.com/a.mp3"
        assert voice_body["audio_duration"] == 12
        assert voice_body["sticker_ids"] == ["paw"]
        assert await balance(client, owner_token) == 125

        reply = await client.post(
            comment_url,
            headers=other,
            json={"body": "回复顶层", "parent_id": top_body["id"]},
        )
        assert reply.status_code == 200, reply.text
        reply_body = reply.json()["data"]
        assert reply_body["parent_id"] == top_body["id"]
        assert reply_body["reply_to"]["id"] == top_body["author"]["id"]

        nested = await client.post(
            comment_url,
            headers=owner,
            json={"body": "回复的回复", "parent_id": reply_body["id"]},
        )
        assert nested.status_code == 200, nested.text
        nested_body = nested.json()["data"]
        assert nested_body["parent_id"] == top_body["id"]
        assert nested_body["reply_to"]["id"] == reply_body["author"]["id"]
        assert await balance(client, owner_token) == 125

        denied = await client.delete(
            f"{comment_url}/{top_body['id']}",
            headers=other,
        )
        assert_error(denied, 403, "FORBIDDEN", "只能删除自己的评论")

        listed = await client.get(comment_url, headers=owner)
        assert listed.status_code == 200, listed.text
        ids = [item["id"] for item in listed.json()["data"]["items"]]
        assert ids == [top_body["id"], voice_body["id"], reply_body["id"], nested_body["id"]]
        assert listed.json()["data"]["total"] == 4

        removed = await client.delete(f"{comment_url}/{top_body['id']}", headers=owner)
        assert removed.status_code == 200, removed.text
        assert removed.json()["data"]["ok"] is True
        assert removed.json()["data"]["comment_count"] == 3
        after = await client.get(comment_url, headers=owner)
        rows = {item["id"]: item for item in after.json()["data"]["items"]}
        assert top_body["id"] not in rows
        assert rows[reply_body["id"]]["parent_id"] is None
        assert rows[nested_body["id"]]["parent_id"] is None
        assert rows[reply_body["id"]]["body"] == "回复顶层"

        removed_reply = await client.delete(f"{comment_url}/{reply_body['id']}", headers=owner)
        assert removed_reply.status_code == 200, removed_reply.text
        assert removed_reply.json()["data"]["comment_count"] == 2
        left = await client.get(comment_url, headers=owner)
        left_ids = [item["id"] for item in left.json()["data"]["items"]]
        assert reply_body["id"] not in left_ids
        assert nested_body["id"] in left_ids


async def test_cannot_report_self_and_duplicate_report_is_noop() -> None:
    async with api() as client:
        owner_token = await login(client, f"community-report-a-{uuid.uuid4().hex}")
        other_token = await login(client, f"community-report-b-{uuid.uuid4().hex}")
        created = await create_post(client, owner_token, title="举报帖")
        assert created.status_code == 200, created.text
        post_id = created.json()["data"]["id"]
        comment = await client.post(
            f"/api/v1/community/post/{post_id}/comment",
            headers=bearer(owner_token),
            json={"body": "不要举报我"},
        )
        assert comment.status_code == 200, comment.text
        comment_id = comment.json()["data"]["id"]
        report_url = f"/api/v1/community/post/{post_id}/comment/{comment_id}/report"

        own = await client.post(report_url, headers=bearer(owner_token), json={"reason": "spam"})
        assert_error(own, 403, "FORBIDDEN", "不能举报自己的评论")
        bad = await client.post(report_url, headers=bearer(other_token), json={"reason": "nope"})
        assert_error(bad, 400, "VALIDATION", "请选择举报原因")
        first = await client.post(report_url, headers=bearer(other_token), json={"reason": "spam"})
        second = await client.post(report_url, headers=bearer(other_token), json={"reason": "abuse"})
        assert first.status_code == 200, first.text
        assert second.status_code == 200, second.text
        assert first.json()["data"] == {"ok": True}
        assert second.json()["data"] == {"ok": True}

    async with SessionFactory() as session:
        count = await session.scalar(select(func.count()).select_from(CommentReport))
    assert int(count or 0) == 1


async def test_follow_rules_lists_and_following_tab() -> None:
    async with api() as client:
        owner_token = await login(client, f"community-follow-a-{uuid.uuid4().hex}")
        other_token = await login(client, f"community-follow-b-{uuid.uuid4().hex}")
        owner = bearer(owner_token)
        other = bearer(other_token)
        owner_id = str(user_id_of(owner_token))
        other_id = str(user_id_of(other_token))
        await client.patch("/api/v1/me", headers=other, json={"nickname": "对方", "avatar_url": None})

        for payload in ({}, {"user_id": ""}, {"user_id": "   "}):
            missing = await client.post("/api/v1/community/follow", headers=owner, json=payload)
            assert_error(missing, 400, "VALIDATION", "缺少 user_id")
        self_follow = await client.post(
            "/api/v1/community/follow",
            headers=owner,
            json={"user_id": owner_id},
        )
        assert_error(self_follow, 400, "VALIDATION", "不能关注自己")
        unknown = await client.post(
            "/api/v1/community/follow",
            headers=owner,
            json={"user_id": str(uuid.uuid4())},
        )
        assert_error(unknown, 404, "NOT_FOUND", "用户不存在")

        created = await create_post(client, other_token, title="被关注的帖", board="qa")
        assert created.status_code == 200, created.text
        post_id = created.json()["data"]["id"]
        before = await client.get(
            "/api/v1/community/post",
            headers=owner,
            params={"tab": "following"},
        )
        assert post_id not in [item["id"] for item in before.json()["data"]["items"]]

        followed = await client.post("/api/v1/community/follow", headers=owner, json={"user_id": other_id})
        assert followed.status_code == 200, followed.text
        assert followed.json()["data"] == {"ok": True}
        again = await client.post("/api/v1/community/follow", headers=owner, json={"user_id": other_id})
        assert_error(again, 409, "CONFLICT", "已经关注")

        following = await client.get("/api/v1/community/follow", headers=owner)
        assert following.status_code == 200, following.text
        assert following.json()["data"]["total"] == 1
        assert following.json()["data"]["items"][0]["id"] == other_id
        assert following.json()["data"]["items"][0]["nickname"] == "对方"
        assert set(following.json()["data"]["items"][0]) == AUTHOR_FIELDS
        followers = await client.get("/api/v1/community/follower", headers=other)
        assert followers.json()["data"]["total"] == 1
        assert followers.json()["data"]["items"][0]["id"] == owner_id

        tab = await client.get("/api/v1/community/post", headers=owner, params={"tab": "following"})
        tab_ids = [item["id"] for item in tab.json()["data"]["items"]]
        assert post_id in tab_ids
        assert tab.json()["data"]["items"][tab_ids.index(post_id)]["followed"] is True

        removed = await client.delete(f"/api/v1/community/follow/{other_id}", headers=owner)
        assert removed.status_code == 200, removed.text
        assert removed.json()["data"] == {"ok": True}
        again_removed = await client.delete(f"/api/v1/community/follow/{other_id}", headers=owner)
        assert again_removed.json()["data"] == {"ok": True}
        empty = await client.get("/api/v1/community/follow", headers=owner)
        assert empty.json()["data"]["total"] == 0
        empty_followers = await client.get("/api/v1/community/follower", headers=other)
        assert empty_followers.json()["data"]["total"] == 0


async def test_favorite_list_and_search() -> None:
    token_bit = uuid.uuid4().hex[:8]
    topic = f"海{token_bit}边"
    title = f"西瓜-{token_bit}"
    async with api() as client:
        token = await login(client, f"community-search-{uuid.uuid4().hex}")
        headers = bearer(token)
        matched = await create_post(
            client,
            token,
            title=title,
            body="橙子正文",
            topic_names=[topic],
            board="share",
        )
        assert matched.status_code == 200, matched.text
        post_id = matched.json()["data"]["id"]
        other = await create_post(client, token, title="别的帖子", body="无关", board="qa")
        assert other.status_code == 200, other.text

        by_title = await client.get("/api/v1/community/post", headers=headers, params={"q": title})
        assert [item["id"] for item in by_title.json()["data"]["items"]] == [post_id]
        by_body = await client.get("/api/v1/community/post", headers=headers, params={"q": "橙子"})
        assert post_id in [item["id"] for item in by_body.json()["data"]["items"]]
        by_topic_q = await client.get(
            "/api/v1/community/post",
            headers=headers,
            params={"q": token_bit},
        )
        assert post_id in [item["id"] for item in by_topic_q.json()["data"]["items"]]
        exact = await client.get("/api/v1/community/post", headers=headers, params={"topic": topic})
        assert [item["id"] for item in exact.json()["data"]["items"]] == [post_id]
        prefix = await client.get(
            "/api/v1/community/post",
            headers=headers,
            params={"topic": f"海{token_bit}"},
        )
        assert post_id not in [item["id"] for item in prefix.json()["data"]["items"]]
        missing = await client.get(
            "/api/v1/community/post",
            headers=headers,
            params={"q": f"不存在-{uuid.uuid4().hex}"},
        )
        assert missing.json()["data"]["total"] == 0
        board = await client.get("/api/v1/community/post", headers=headers, params={"tab": "qa"})
        assert other.json()["data"]["id"] in [item["id"] for item in board.json()["data"]["items"]]
        assert post_id not in [item["id"] for item in board.json()["data"]["items"]]

        saved = await client.post(
            f"/api/v1/community/post/{post_id}/favorite",
            headers=headers,
            json={},
        )
        assert saved.status_code == 200, saved.text
        assert saved.json()["data"]["favorited"] is True
        assert saved.json()["data"]["favorite_count"] == 1
        favorites = await client.get("/api/v1/community/post/favorite", headers=headers)
        assert favorites.status_code == 200, favorites.text
        assert [item["id"] for item in favorites.json()["data"]["items"]] == [post_id]
        assert favorites.json()["data"]["items"][0]["favorited"] is True

        cleared = await client.post(
            f"/api/v1/community/post/{post_id}/favorite",
            headers=headers,
            json={},
        )
        assert cleared.json()["data"]["favorited"] is False
        assert cleared.json()["data"]["favorite_count"] == 0
        empty = await client.get("/api/v1/community/post/favorite", headers=headers)
        assert empty.json()["data"]["total"] == 0


async def test_profile_counts_and_publish_album_show() -> None:
    async with api() as client:
        owner_token = await login(client, f"community-counts-a-{uuid.uuid4().hex}")
        other_token = await login(client, f"community-counts-b-{uuid.uuid4().hex}")
        owner_id = user_id_of(owner_token)
        other_id = user_id_of(other_token)
        created = await create_post(client, owner_token, title="统计帖", board="daily")
        assert created.status_code == 200, created.text
        post_id = created.json()["data"]["id"]
        liked = await client.post(
            f"/api/v1/community/post/{post_id}/like",
            headers=bearer(other_token),
            json={},
        )
        assert liked.status_code == 200, liked.text
        followed = await client.post(
            "/api/v1/community/follow",
            headers=bearer(owner_token),
            json={"user_id": str(other_id)},
        )
        assert followed.status_code == 200, followed.text

        async with opened_service() as (service, session):
            owner_counts = await service.profile_counts(owner_id)
            other_counts = await service.profile_counts(other_id)
            assert owner_counts.post_count == 1
            assert owner_counts.like_received_count == 1
            assert owner_counts.following_count == 1
            assert owner_counts.follower_count == 0
            assert other_counts.post_count == 0
            assert other_counts.like_received_count == 0
            assert other_counts.following_count == 0
            assert other_counts.follower_count == 1

            await service.publish_album_show(
                owner_id,
                title="相册同步",
                body="去公园",
                image_urls=["https://example.com/1.jpg"],
                topic_names=["生活"],
            )
            await session.commit()

        assert await balance(client, owner_token) == 140
        listed = await client.get(
            "/api/v1/community/post",
            headers=bearer(owner_token),
            params={"tab": "show", "q": "相册同步"},
        )
        assert listed.status_code == 200, listed.text
        items = listed.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["board"] == "show"
        assert items[0]["status"] == "published"
        assert items[0]["title"] == "相册同步"
        assert items[0]["body"] == "去公园"
        assert items[0]["image_urls"] == ["https://example.com/1.jpg"]
        assert items[0]["topic_names"] == ["生活"]
        assert items[0]["author"]["id"] == str(owner_id)

        async with opened_service() as (service, _session):
            recounted = await service.profile_counts(owner_id)
        assert recounted.post_count == 2
        assert recounted.like_received_count == 1
        assert recounted.following_count == 1
