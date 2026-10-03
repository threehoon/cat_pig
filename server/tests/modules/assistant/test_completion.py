import json
import logging

import httpx
import pytest

from app.core.exceptions import AppError
from app.modules.assistant.completion import INSTRUCTIONS, StaticCompleter
from app.modules.assistant.deps import get_completer
from app.modules.assistant.llm_config import get_llm_config
from app.modules.assistant.providers.openai_chat import OpenAIChatCompleter, chat_text
from app.modules.assistant.providers.xai import XaiCompleter, reply_text
from app.modules.assistant.service import GENERATED_ANSWER
from tests.modules.assistant.test_ask import ask, assistant_app, login


SECRET = "super-secret-key"


def test_reply_text_skips_reasoning() -> None:
    text = reply_text(
        {
            "output": [
                {"type": "reasoning", "encrypted_content": "secret"},
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "  你好呀  "}],
                },
            ]
        }
    )
    assert text == "你好呀"


def test_reply_text_rejects_empty() -> None:
    with pytest.raises(ValueError):
        reply_text({"output": [{"type": "reasoning"}]})


def test_chat_text_reads_message_content() -> None:
    text = chat_text(
        {"choices": [{"message": {"role": "assistant", "content": "  你好呀  "}}]}
    )
    assert text == "你好呀"


async def test_xai_completer_posts_responses() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": "你好呀"}],
                    }
                ]
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    completer = XaiCompleter("test-key", "https://api.x.ai/v1/", "grok-4.7", client=client)
    answer = await completer.complete("你好")
    await client.aclose()

    assert answer == "你好呀"
    assert seen["url"] == "https://api.x.ai/v1/responses"
    assert seen["authorization"] == "Bearer test-key"
    assert seen["body"] == {
        "model": "grok-4.7",
        "store": False,
        "reasoning": {"effort": "low"},
        "instructions": INSTRUCTIONS,
        "input": "你好",
    }


async def test_openai_completer_posts_chat_completions() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"role": "assistant", "content": "你好呀"}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    completer = OpenAIChatCompleter(
        "test-key",
        "https://relay.example/v1/",
        "demo-model",
        client=client,
    )
    answer = await completer.complete("你好")
    await client.aclose()

    assert answer == "你好呀"
    assert seen["url"] == "https://relay.example/v1/chat/completions"
    assert seen["authorization"] == "Bearer test-key"
    assert seen["body"] == {
        "model": "demo-model",
        "messages": [
            {"role": "system", "content": INSTRUCTIONS},
            {"role": "user", "content": "你好"},
        ],
    }


async def test_upstream_failure_hides_the_key(caplog: pytest.LogCaptureFixture) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": request.headers["authorization"]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    completer = XaiCompleter(SECRET, "https://api.x.ai/v1", "grok-4.7", client=client)
    with caplog.at_level(logging.WARNING):
        with pytest.raises(AppError) as caught:
            await completer.complete("你好")
    await client.aclose()

    assert caught.value.status_code == 502
    assert caught.value.message == "请稍后再试"
    assert SECRET not in caught.value.message
    assert SECRET not in caplog.text


def test_config_repr_hides_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XAI_API_KEY", SECRET)
    monkeypatch.setenv("OPENAI_API_KEY", "relay-secret-key")
    get_llm_config.cache_clear()
    config = get_llm_config()

    visible = f"{config!r} {config} {config.model_dump(mode='json')}"
    assert SECRET not in visible
    assert "relay-secret-key" not in visible
    assert config.xai_api_key.get_secret_value() == SECRET
    assert config.model_dump(mode="json")["xai_api_key"] == ""
    assert config.model_dump(mode="json")["openai_api_key"] == ""


def test_off_keeps_the_fixed_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASSISTANT_LLM", "off")
    monkeypatch.setenv("XAI_API_KEY", SECRET)
    get_llm_config.cache_clear()
    completer = get_completer()
    assert isinstance(completer, StaticCompleter)


async def test_static_completer_returns_fixed_sentence() -> None:
    completer = StaticCompleter(GENERATED_ANSWER)
    assert await completer.complete("你好") == GENERATED_ANSWER


def test_xai_switch_selects_official(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASSISTANT_LLM", "xai")
    monkeypatch.setenv("XAI_API_KEY", "test-key")
    monkeypatch.setenv("XAI_MODEL", "grok-4.7")
    get_llm_config.cache_clear()
    completer = get_completer()
    assert isinstance(completer, XaiCompleter)


def test_openai_switch_selects_compatible(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASSISTANT_LLM", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "demo-model")
    get_llm_config.cache_clear()
    completer = get_completer()
    assert isinstance(completer, OpenAIChatCompleter)


async def test_missing_key_does_not_leak(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("ASSISTANT_LLM", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "demo-model")
    get_llm_config.cache_clear()
    completer = get_completer()
    with caplog.at_level(logging.WARNING):
        with pytest.raises(AppError) as caught:
            await completer.complete("你好")

    assert caught.value.message == "请稍后再试"
    assert "缺少密钥" in caplog.text
    assert SECRET not in caplog.text
    assert "relay.example" not in caught.value.message


async def test_unknown_provider_does_not_log_the_value(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("ASSISTANT_LLM", SECRET)
    get_llm_config.cache_clear()
    completer = get_completer()
    with caplog.at_level(logging.WARNING):
        with pytest.raises(AppError) as caught:
            await completer.complete("你好")

    assert caught.value.message == "请稍后再试"
    assert SECRET not in caplog.text
    assert "未知提供方" in caplog.text


async def test_provider_without_key_returns_busy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASSISTANT_LLM", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://relay.example/v1")
    monkeypatch.setenv("OPENAI_MODEL", "demo-model")
    get_llm_config.cache_clear()
    async with assistant_app() as client:
        token = await login(client, "missing-llm-key")
        response = await ask(
            client,
            token,
            {"question": "你好", "conversation_id": None},
        )

    assert response.status_code == 502
    assert response.json()["error"]["message"] == "请稍后再试"
    assert "relay.example" not in response.text
    assert SECRET not in response.text
