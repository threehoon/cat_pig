import logging
from typing import Protocol

import httpx

from app.core.exceptions import AppError, ErrorCode


logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "你是小程序里的宠物伙伴，名字叫小x。"
    "用口语中文回答，像当面聊天，一般两三句，先接住对方刚说的话。"
    "不要用「我是小x。这是常识说明」开头，也不要先写免责声明。"
    "日常问题按常识回答。不要下诊断，不要说出药名或剂量。"
    "界面已经标了仅供参考，正文里不要再写这四个字。"
)
BUSY_MESSAGE = "请稍后再试"
TIMEOUT_SECONDS = 45.0


class Completer(Protocol):
    async def complete(self, question: str) -> str: ...


class StaticCompleter:
    def __init__(self, answer: str) -> None:
        self._answer = answer

    async def complete(self, question: str) -> str:
        del question
        return self._answer


class UnavailableCompleter:
    def __init__(self, provider: str, reason: str) -> None:
        self._provider = provider
        self._reason = reason

    async def complete(self, question: str) -> str:
        del question
        logger.warning("assistant llm %s: %s", self._provider, self._reason)
        raise _busy()


async def post_json(
    *,
    url: str,
    api_key: str,
    payload: dict[str, object],
    client: httpx.AsyncClient | None,
) -> httpx.Response:
    headers = {"Authorization": f"Bearer {api_key}"}
    if client is not None:
        return await client.post(url, headers=headers, json=payload)
    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as owned:
        return await owned.post(url, headers=headers, json=payload)


def reject_upstream(provider: str, status: str) -> AppError:
    logger.warning("assistant llm %s failed status=%s", provider, status)
    return _busy()


def _busy() -> AppError:
    return AppError(ErrorCode.INTERNAL, BUSY_MESSAGE, 502)
