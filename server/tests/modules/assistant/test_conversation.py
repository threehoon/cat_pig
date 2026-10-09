import importlib.util
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import func, select

from app.core.db import SessionFactory
from app.core.exceptions import AppError, ErrorCode
from app.core.security import decode_access_token
from app.modules.assistant.completion import Turn
from app.modules.assistant.ingest import SEED_DIR, ingest_directory
from app.modules.assistant.models import Conversation, ConversationMessage
from app.modules.assistant.service import GENERATED_ANSWER, REFUSE_ANSWER
from tests.modules.assistant.test_ask import ask, assistant_app, bearer, login


@pytest_asyncio.fixture
async def published_seeds() -> None:
    async with SessionFactory() as session:
        await ingest_directory(session, SEED_DIR)
        await session.commit()


async def _counts() -> tuple[int, int]:
    async with SessionFactory() as session:
        conversations = await session.scalar(select(func.count()).select_from(Conversation))
        messages = await session.scalar(select(func.count()).select_from(ConversationMessage))
    return int(conversations or 0), int(messages or 0)


class RecordingCompleter:
    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.calls: list[tuple[str, list[Turn]]] = []

    async def complete(self, question: str, history: object = ()) -> str:
        turns = list(history) if isinstance(history, list | tuple) else []
        self.calls.append((question, turns))
        return self.answer


class BoomCompleter:
    async def complete(self, question: str, history: object = ()) -> str:
        del question, history
        raise AppError(ErrorCode.INTERNAL, "请稍后再试", 502)


async def test_second_turn_sends_the_first_exchange(monkeypatch: pytest.MonkeyPatch) -> None:
    completer = RecordingCompleter(GENERATED_ANSWER)
    monkeypatch.setattr("app.modules.assistant.deps.get_completer", lambda: completer)
    async with assistant_app() as client:
        token = await login(client, "thread-user")
        first = await ask(client, token, {"question": "你好", "conversation_id": None})
        conversation_id = first.json()["data"]["conversation_id"]
        second = await ask(
            client,
            token,
            {"question": "那猫呢", "conversation_id": conversation_id},
        )

    assert second.status_code == 200
    assert completer.calls[0] == ("你好", [])
    assert completer.calls[1] == (
        "那猫呢",
        [Turn("user", "你好"), Turn("assistant", GENERATED_ANSWER)],
    )


async def test_refusal_is_stored_and_shown_to_the_next_turn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    completer = RecordingCompleter("换个话题聊聊")
    monkeypatch.setattr("app.modules.assistant.deps.get_completer", lambda: completer)
    async with assistant_app() as client:
        token = await login(client, "refuse-history")
        refused = await ask(
            client,
            token,
            {"question": "猫咪发烧该吃什么药", "conversation_id": None},
        )
        conversation_id = refused.json()["data"]["conversation_id"]
        followed = await ask(
            client,
            token,
            {"question": "那今天天气怎么样", "conversation_id": conversation_id},
        )
        messages = await client.get(
            f"/api/v1/assistant/conversation/{conversation_id}/message",
            headers=bearer(token),
        )

    assert refused.status_code == 200
    assert followed.status_code == 200
    assert completer.calls == [
        (
            "那今天天气怎么样",
            [
                Turn("user", "猫咪发烧该吃什么药"),
                Turn("assistant", REFUSE_ANSWER),
            ],
        )
    ]
    body = messages.json()["data"]
    assert [item["text"] for item in body["items"]] == [
        "猫咪发烧该吃什么药",
        REFUSE_ANSWER,
        "那今天天气怎么样",
        "换个话题聊聊",
    ]
    assert "body" not in body["items"][0]
    assert body["items"][0]["source"] is None
    assert body["items"][1]["source"] == "generated"


async def test_knowledge_answer_is_visible_on_the_next_turn(
    monkeypatch: pytest.MonkeyPatch,
    published_seeds: None,
) -> None:
    del published_seeds
    completer = RecordingCompleter("猫也要阴凉和水")
    monkeypatch.setattr("app.modules.assistant.deps.get_completer", lambda: completer)
    async with assistant_app() as client:
        token = await login(client, "knowledge-history")
        first = await ask(
            client,
            token,
            {"question": "夏天怎么给狗降温", "conversation_id": None},
        )
        data = first.json()["data"]
        conversation_id = data["conversation_id"]
        await ask(client, token, {"question": "那猫呢", "conversation_id": conversation_id})
        messages = await client.get(
            f"/api/v1/assistant/conversation/{conversation_id}/message",
            headers=bearer(token),
        )

    assert data["source"] == "knowledge"
    assert completer.calls == [
        ("那猫呢", [Turn("user", "夏天怎么给狗降温"), Turn("assistant", data["answer"])])
    ]
    assistant = messages.json()["data"]["items"][1]
    assert assistant["text"] == data["answer"]
    assert assistant["source"] == "knowledge"
    assert assistant["citations"]
    assert set(assistant["citations"][0]) == {"id", "title", "snippet"}


async def test_failed_completion_writes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.assistant.deps.get_completer", lambda: BoomCompleter())
    async with assistant_app() as client:
        token = await login(client, "boom-user")
        response = await ask(client, token, {"question": "你好", "conversation_id": None})

    assert response.status_code == 502
    assert await _counts() == (0, 0)


async def test_list_hides_other_users_and_empty_rows() -> None:
    async with assistant_app() as client:
        owner = await login(client, "owner-user")
        other = await login(client, "other-user")
        created = await ask(client, owner, {"question": "第一句", "conversation_id": None})
        conversation_id = created.json()["data"]["conversation_id"]
        await ask(client, owner, {"question": "第二句", "conversation_id": conversation_id})
        owner_id = uuid.UUID(decode_access_token(owner))
        async with SessionFactory() as session:
            session.add(Conversation(user_id=owner_id))
            await session.commit()
        listing = await client.get(
            "/api/v1/assistant/conversation",
            headers=bearer(owner),
        )
        foreign = await client.get(
            "/api/v1/assistant/conversation",
            headers=bearer(other),
        )
        missing = await client.get(
            f"/api/v1/assistant/conversation/{conversation_id}/message",
            headers=bearer(other),
        )

    assert listing.status_code == 200
    page = listing.json()["data"]
    assert page["total"] == 1
    assert page["items"][0]["title"] == "第一句"
    assert page["items"][0]["updated_at"].endswith("Z")
    assert foreign.status_code == 200
    assert foreign.json()["data"]["items"] == []
    assert foreign.json()["data"]["total"] == 0
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"


async def test_successful_reply_moves_updated_at() -> None:
    async with assistant_app() as client:
        token = await login(client, "stamp-user")
        created = await ask(client, token, {"question": "你好", "conversation_id": None})
        conversation_id = uuid.UUID(created.json()["data"]["conversation_id"])
        async with SessionFactory() as session:
            row = await session.get(Conversation, conversation_id)
            assert row is not None
            row.updated_at = datetime(2000, 1, 1, tzinfo=UTC)
            await session.commit()
        await ask(
            client,
            token,
            {"question": "猫咪发烧该吃什么药", "conversation_id": str(conversation_id)},
        )
        listing = await client.get(
            "/api/v1/assistant/conversation",
            headers=bearer(token),
        )

    assert listing.json()["data"]["items"][0]["updated_at"].startswith("2000") is False


async def test_missing_conversation_message_is_not_found() -> None:
    async with assistant_app() as client:
        token = await login(client, "missing-thread-user")
        response = await client.get(
            f"/api/v1/assistant/conversation/{uuid.uuid4()}/message",
            headers=bearer(token),
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


async def test_message_path_rejects_a_bad_id() -> None:
    async with assistant_app() as client:
        token = await login(client, "bad-id-user")
        response = await client.get(
            "/api/v1/assistant/conversation/not-a-uuid/message",
            headers=bearer(token),
        )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION"


def test_message_migration_revises_video_task() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "alembic"
        / "versions"
        / "0011_conversation_message.py"
    )
    spec = importlib.util.spec_from_file_location("rev_0011_conversation_message", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "0011_conversation_message"
    assert module.down_revision == "0010_video_task"
