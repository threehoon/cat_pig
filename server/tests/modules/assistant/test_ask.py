import importlib.util
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient, Response

from app.core.db import SessionFactory
from app.core.security import create_access_token
from app.main import create_app
from app.modules.assistant.ingest import SEED_DIR, ingest_directory


COOLING_TITLE = "夏天给狗降温"
COOLING_SNIPPET = "避开正午出门，室内通风，提供阴凉饮水和湿毛巾擦身，不要用冰水浇身。"
COOLING_BODY = (
    "夏天给狗降温，先避开正午出门，改在清晨或傍晚。屋里通风、留阴凉处，随时有干净凉水。"
    "可以用湿毛巾擦肚皮和脚垫散热，不要浇冰水、不要把狗关在停驶的车里。"
    "我是小x，这是说明书里的日常护理，不能代替兽医。"
)
REFUSE_ANSWER = (
    "我是小x。知识库里没有足够依据回答看病或用药的问题。"
    "请带毛孩子去医院，不要自行用药。我不会编诊断、药名或剂量。"
)
GENERATED_ANSWER = "我是小x。这是常识说明，仅供参考，不能代替专业意见。"
SUGGESTIONS = (
    ("e1111111-1111-1111-1111-111111111111", "夏天怎么给狗降温"),
    ("e2222222-2222-2222-2222-222222222222", "附近有没有靠谱的宠物医院"),
    ("e3333333-3333-3333-3333-333333333333", "为什么天空是蓝的"),
    ("e4444444-4444-4444-4444-444444444444", "猫咪发烧该吃什么药"),
)
REFUSE_WORDS = ("发烧", "吃药", "用药", "开药", "剂量", "诊断", "拉肚子", "什么药")
ASK_FIELDS = {"conversation_id", "answer", "source", "citations", "related_posts"}


def assistant_app() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=create_app()),
        base_url="http://test",
    )


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, code: str) -> str:
    response = await client.post("/api/v1/auth/login", json={"code": code})
    assert response.status_code == 200
    return response.json()["data"]["token"]


async def ask(client: AsyncClient, token: str, payload: dict[str, object]) -> Response:
    return await client.post(
        "/api/v1/assistant/ask",
        headers=bearer(token),
        json=payload,
    )


@pytest_asyncio.fixture
async def published_seeds() -> None:
    async with SessionFactory() as session:
        await ingest_directory(session, SEED_DIR)
        await session.commit()


def test_conversation_migration_revises_knowledge() -> None:
    path = (
        Path(__file__).resolve().parents[3]
        / "alembic"
        / "versions"
        / "0004_assistant_conversation.py"
    )
    spec = importlib.util.spec_from_file_location("rev_0004_assistant_conversation", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load migration {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.revision == "0004_assistant_conversation"
    assert module.down_revision == "0003_assistant_knowledge"


async def test_suggestion_requires_token() -> None:
    async with assistant_app() as client:
        response = await client.get("/api/v1/assistant/suggestion")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_ask_requires_token() -> None:
    async with assistant_app() as client:
        response = await client.post(
            "/api/v1/assistant/ask",
            json={"question": "夏天怎么给狗降温", "conversation_id": None},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_suggestion_lists_four_hardcoded_questions() -> None:
    async with assistant_app() as client:
        token = await login(client, "suggestion-user")
        response = await client.get(
            "/api/v1/assistant/suggestion",
            headers=bearer(token),
        )

    body = response.json()
    assert response.status_code == 200
    assert set(body) == {"data"}
    page = body["data"]
    assert set(page) == {"items", "total", "page", "page_size"}
    assert page["total"] == 4
    assert page["page"] == 1
    assert page["page_size"] == 20
    assert [(item["id"], item["question"]) for item in page["items"]] == list(SUGGESTIONS)


async def test_suggestion_paginates_in_memory() -> None:
    async with assistant_app() as client:
        token = await login(client, "suggestion-page")
        response = await client.get(
            "/api/v1/assistant/suggestion",
            headers=bearer(token),
            params={"page": 2, "page_size": 2},
        )
        beyond = await client.get(
            "/api/v1/assistant/suggestion",
            headers=bearer(token),
            params={"page": 3, "page_size": 2},
        )

    page = response.json()["data"]
    assert response.status_code == 200
    assert page["total"] == 4
    assert page["page"] == 2
    assert page["page_size"] == 2
    assert [(item["id"], item["question"]) for item in page["items"]] == list(SUGGESTIONS[2:])
    assert beyond.status_code == 200
    assert beyond.json()["data"]["items"] == []
    assert beyond.json()["data"]["total"] == 4


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"conversation_id": None},
        {"question": "", "conversation_id": None},
        {"question": "   ", "conversation_id": None},
        {"question": "夏天怎么给狗降温", "conversation_id": "not-a-uuid"},
    ],
)
async def test_ask_rejects_blank_or_malformed_input(payload: dict[str, object]) -> None:
    async with assistant_app() as client:
        token = await login(client, "validation-user")
        response = await ask(client, token, payload)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION"


async def test_invalid_subject_is_unauthorized_not_internal() -> None:
    async with assistant_app() as client:
        response = await ask(
            client,
            create_access_token("not-a-uuid"),
            {"question": "你好", "conversation_id": None},
        )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_medicine_question_refuses_and_reuses_conversation() -> None:
    payload = {"question": "猫咪发烧该吃什么药", "conversation_id": None}
    async with assistant_app() as client:
        token = await login(client, "refuse-user")
        first = await ask(client, token, payload)
        conversation_id = first.json()["data"]["conversation_id"]
        second = await ask(
            client,
            token,
            {"question": "猫咪发烧该吃什么药", "conversation_id": conversation_id},
        )

    for response in (first, second):
        assert response.status_code == 200
        data = response.json()["data"]
        assert set(data) == ASK_FIELDS
        assert data["source"] == "generated"
        assert data["answer"] == REFUSE_ANSWER
        assert data["citations"] == []
        assert data["related_posts"] == []
        assert data["conversation_id"] == conversation_id
    uuid.UUID(conversation_id)


@pytest.mark.parametrize("word", REFUSE_WORDS)
async def test_each_refuse_word_short_circuits(word: str) -> None:
    async with assistant_app() as client:
        token = await login(client, f"refuse-{word}")
        response = await ask(
            client,
            token,
            {"question": f"测试{word}", "conversation_id": None},
        )

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["source"] == "generated"
    assert data["answer"] == REFUSE_ANSWER
    assert data["citations"] == []
    assert data["related_posts"] == []


async def test_cooling_question_returns_seed_body(published_seeds: None) -> None:
    async with assistant_app() as client:
        token = await login(client, "cooling-user")
        response = await ask(
            client,
            token,
            {"question": "夏天怎么给狗降温", "conversation_id": None},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["source"] == "knowledge"
    assert data["answer"] == COOLING_BODY
    assert data["related_posts"] == []
    assert len(data["citations"]) == 1
    citation = data["citations"][0]
    uuid.UUID(citation["id"])
    assert citation["title"] == COOLING_TITLE
    assert citation["snippet"] == COOLING_SNIPPET


@pytest.mark.parametrize(
    "question",
    ["今天上证指数多少", "附近有没有靠谱的宠物医院", "为什么天空是蓝的"],
)
async def test_unrelated_questions_stay_short_generated(
    published_seeds: None,
    question: str,
) -> None:
    async with assistant_app() as client:
        token = await login(client, f"generated-{question}")
        response = await ask(
            client,
            token,
            {"question": question, "conversation_id": None},
        )

    data = response.json()["data"]
    assert response.status_code == 200
    assert data["source"] == "generated"
    assert data["answer"] == GENERATED_ANSWER
    assert data["citations"] == []
    assert data["related_posts"] == []


async def test_null_conversation_id_is_stable_when_sent_back() -> None:
    async with assistant_app() as client:
        token = await login(client, "conversation-user")
        first = await ask(
            client,
            token,
            {"question": "今天天气怎么样", "conversation_id": None},
        )
        conversation_id = first.json()["data"]["conversation_id"]
        second = await ask(
            client,
            token,
            {"question": "今天天气怎么样", "conversation_id": conversation_id},
        )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["data"]["conversation_id"] == conversation_id
    uuid.UUID(conversation_id)


async def test_other_users_conversation_is_not_found() -> None:
    async with assistant_app() as client:
        owner = await login(client, "owner-code")
        created = await ask(
            client,
            owner,
            {"question": "今天天气怎么样", "conversation_id": None},
        )
        conversation_id = created.json()["data"]["conversation_id"]
        other = await login(client, "other-code")
        response = await ask(
            client,
            other,
            {"question": "今天天气怎么样", "conversation_id": conversation_id},
        )

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "NOT_FOUND",
        "message": "Conversation not found",
    }


async def test_missing_conversation_is_not_found() -> None:
    async with assistant_app() as client:
        token = await login(client, "missing-conversation")
        response = await ask(
            client,
            token,
            {"question": "今天天气怎么样", "conversation_id": str(uuid.uuid4())},
        )

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "NOT_FOUND",
        "message": "Conversation not found",
    }
