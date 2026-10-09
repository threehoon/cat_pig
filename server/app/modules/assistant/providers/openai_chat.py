from collections.abc import Sequence

import httpx

from app.modules.assistant.completion import (
    INSTRUCTIONS,
    Turn,
    post_json,
    reject_upstream,
)


PROVIDER = "openai"


class OpenAIChatCompleter:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._client = client

    async def complete(self, question: str, history: Sequence[Turn] = ()) -> str:
        messages: list[dict[str, str]] = [{"role": "system", "content": INSTRUCTIONS}]
        for turn in history:
            messages.append({"role": turn.role, "content": turn.content})
        messages.append({"role": "user", "content": question})
        payload = {
            "model": self._model,
            "messages": messages,
        }
        try:
            response = await post_json(
                url=f"{self._base_url}/chat/completions",
                api_key=self._api_key,
                payload=payload,
                client=self._client,
            )
        except httpx.HTTPError as exc:
            raise reject_upstream(PROVIDER, "transport") from exc
        if response.status_code >= 400:
            raise reject_upstream(PROVIDER, str(response.status_code))
        try:
            return chat_text(response.json())
        except (ValueError, TypeError) as exc:
            raise reject_upstream(PROVIDER, "bad-body") from exc


def chat_text(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("reply payload is not an object")
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("reply choices are missing")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("reply choice is not an object")
    message = first.get("message")
    if not isinstance(message, dict):
        raise ValueError("reply message is missing")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("reply text is empty")
    return content.strip()
