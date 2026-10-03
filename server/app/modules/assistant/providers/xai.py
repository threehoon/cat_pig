import httpx

from app.modules.assistant.completion import (
    INSTRUCTIONS,
    post_json,
    reject_upstream,
)


PROVIDER = "xai"


class XaiCompleter:
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

    async def complete(self, question: str) -> str:
        payload = {
            "model": self._model,
            "store": False,
            "reasoning": {"effort": "low"},
            "instructions": INSTRUCTIONS,
            "input": question,
        }
        try:
            response = await post_json(
                url=f"{self._base_url}/responses",
                api_key=self._api_key,
                payload=payload,
                client=self._client,
            )
        except httpx.HTTPError as exc:
            raise reject_upstream(PROVIDER, "transport") from exc
        if response.status_code >= 400:
            raise reject_upstream(PROVIDER, str(response.status_code))
        try:
            return reply_text(response.json())
        except (ValueError, TypeError) as exc:
            raise reject_upstream(PROVIDER, "bad-body") from exc


def reply_text(payload: object) -> str:
    if not isinstance(payload, dict):
        raise ValueError("reply payload is not an object")
    output = payload.get("output")
    if not isinstance(output, list):
        raise ValueError("reply output is missing")
    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "output_text":
                continue
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
    if not parts:
        raise ValueError("reply text is empty")
    return "\n".join(parts)
