import logging
from collections.abc import Sequence
from typing import NamedTuple, Protocol

import httpx

from app.core.exceptions import AppError, ErrorCode


logger = logging.getLogger(__name__)

INSTRUCTIONS = (
    "你是小程序里的宠物伙伴，名字叫小x。"
    "用口语中文回答，像当面聊天，一般两三句。"
    "如果上面有更早的对话，顺着接，不要每句都复述上一句。"
    "没有更早对话时，直接回答这一句。"
    "不要用「我是小x。这是常识说明」开头，也不要先写免责声明。"
    "日常问题按常识回答。不要下诊断，不要说出药名或剂量。"
    "正文里不要写「仅供参考」。"
)
BUSY_MESSAGE = "请稍后再试"
# 一个 float 同时是 connect / read / write / pool 的上限，四段各自计时，没有总时长。
# read 按下一块数据到来前的等待重计。非流式时首字节不来，大约在这个秒数断开。
# 页面 fail 的 toast 是字面 NETWORK，不保证晚于「请稍后再试」。
# 以后若拆开，把 read 留给模型等待，另外三段另设更短的上限。这次不改这个数字。
TIMEOUT_SECONDS = 45.0


class Turn(NamedTuple):
    role: str
    content: str


class Completer(Protocol):
    async def complete(self, question: str, history: Sequence[Turn] = ()) -> str: ...


class StaticCompleter:
    def __init__(self, answer: str) -> None:
        self._answer = answer

    async def complete(self, question: str, history: Sequence[Turn] = ()) -> str:
        del question, history
        return self._answer


class UnavailableCompleter:
    def __init__(self, provider: str, reason: str) -> None:
        self._provider = provider
        self._reason = reason

    async def complete(self, question: str, history: Sequence[Turn] = ()) -> str:
        del question, history
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
    # status 只进这行日志，不进 AppError。
    logger.warning("assistant llm %s failed status=%s", provider, status)
    return _busy()


def _busy() -> AppError:
    return AppError(ErrorCode.INTERNAL, BUSY_MESSAGE, 502)
