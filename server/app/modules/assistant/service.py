import uuid
from typing import Literal

from app.core.clock import format_utc
from app.core.exceptions import AppError, ErrorCode
from app.core.pagination import PageQuery
from app.core.settings import get_settings
from app.modules.assistant.completion import Completer, Turn
from app.modules.assistant.embeddings import Embedder
from app.modules.assistant.history import model_history
from app.modules.assistant.models import KnowledgeChunk
from app.modules.assistant.repository import ConversationRepository, KnowledgeRepository
from app.modules.assistant.schemas import (
    AssistantAsk,
    AssistantCitation,
    AssistantConversation,
    AssistantMessage,
    AssistantSuggestion,
    ConversationPage,
    MessagePage,
    SuggestionPage,
)
from app.modules.assistant.suggestions import SUGGESTIONS


REFUSE_WORDS = ("发烧", "吃药", "用药", "开药", "剂量", "诊断", "拉肚子", "什么药")
REFUSE_ANSWER = (
    "我是小x。知识库里没有足够依据回答看病或用药的问题。"
    "请带毛孩子去医院，不要自行用药。我不会编诊断、药名或剂量。"
)
GENERATED_ANSWER = "我是小x。这是常识说明，仅供参考，不能代替专业意见。"
TOP_K = 8


def _role(value: str) -> Literal["user", "assistant"]:
    if value == "assistant":
        return "assistant"
    return "user"


def _source(value: str | None) -> Literal["knowledge", "search", "generated"] | None:
    if value == "knowledge" or value == "search" or value == "generated":
        return value
    return None


def _citations(raw: object) -> list[AssistantCitation]:
    if not isinstance(raw, list):
        return []
    items: list[AssistantCitation] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        items.append(
            AssistantCitation(
                id=str(item.get("id", "")),
                title=str(item.get("title", "")),
                snippet=str(item.get("snippet", "")),
            )
        )
    return items


def _citations_from_chunks(
    passing: list[tuple[KnowledgeChunk, float]],
) -> list[AssistantCitation]:
    citations: list[AssistantCitation] = []
    seen: set[uuid.UUID] = set()
    for chunk, _distance in passing:
        article = chunk.article
        if article.id in seen:
            continue
        seen.add(article.id)
        citations.append(
            AssistantCitation(
                id=str(article.id),
                title=article.title,
                snippet=article.snippet,
            )
        )
    return citations


def knowledge_answer(passing: list[tuple[KnowledgeChunk, float]]) -> str:
    article_id = passing[0][0].article_id
    chosen = [chunk for chunk, _distance in passing if chunk.article_id == article_id]
    chosen.sort(key=lambda chunk: chunk.chunk_index)
    return "\n".join(chunk.text.split("\n", 1)[1] for chunk in chosen)


class AssistantService:
    def __init__(
        self,
        knowledge: KnowledgeRepository,
        conversations: ConversationRepository,
        embedder: Embedder,
        completer: Completer,
    ) -> None:
        self._knowledge = knowledge
        self._conversations = conversations
        self._embedder = embedder
        self._completer = completer

    def list_suggestions(self, page: PageQuery) -> SuggestionPage:
        start = (page.page - 1) * page.page_size
        items = [
            AssistantSuggestion(id=item_id, question=question)
            for item_id, question in SUGGESTIONS[start : start + page.page_size]
        ]
        return SuggestionPage(
            items=items,
            total=len(SUGGESTIONS),
            page=page.page,
            page_size=page.page_size,
        )

    async def list_conversations(self, user_id: uuid.UUID, page: PageQuery) -> ConversationPage:
        rows, total = await self._conversations.list_for_user(user_id, page.page, page.page_size)
        items = [
            AssistantConversation(
                id=str(row.id),
                title=row.title or "",
                updated_at=format_utc(row.updated_at),
            )
            for row in rows
        ]
        return ConversationPage(
            items=items,
            total=total,
            page=page.page,
            page_size=page.page_size,
        )

    async def list_messages(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
        page: PageQuery,
    ) -> MessagePage:
        found = await self._conversations.get(conversation_id)
        if found is None or found.user_id != user_id:
            raise AppError(ErrorCode.NOT_FOUND, "Conversation not found", 404)
        rows, total = await self._conversations.list_messages(
            conversation_id,
            page.page,
            page.page_size,
        )
        items = [
            AssistantMessage(
                id=str(row.id),
                role=_role(row.role),
                text=row.body,
                source=_source(row.source),
                citations=_citations(row.citations),
            )
            for row in rows
        ]
        return MessagePage(
            items=items,
            total=total,
            page=page.page,
            page_size=page.page_size,
        )

    async def ask(
        self,
        user_id: uuid.UUID,
        question: str,
        conversation_id: uuid.UUID | None,
    ) -> AssistantAsk:
        stripped = question.strip()
        if not stripped:
            raise AppError(ErrorCode.VALIDATION, "Question is required", 400)

        refused = any(word in stripped for word in REFUSE_WORDS)
        embedding = None if refused else await self._embedder.embed(stripped)
        knowledge_text, citations, prior, existing_id = await self._prepare(
            user_id,
            conversation_id,
            embedding,
        )
        # 释放连接后再等模型。请求结束时的 commit 只提交下面这次写入。
        await self._conversations.commit()

        answer, source, saved_citations = await self._answer(
            stripped,
            refused=refused,
            knowledge_text=knowledge_text,
            citations=citations,
            prior=prior,
        )
        saved = await self._conversations.append_exchange(
            user_id=user_id,
            conversation_id=existing_id,
            question=stripped,
            answer=answer,
            source=source,
            citations=[item.model_dump() for item in saved_citations],
        )
        if saved is None:
            raise AppError(ErrorCode.NOT_FOUND, "Conversation not found", 404)
        return AssistantAsk(
            conversation_id=str(saved),
            answer=answer,
            source=source,
            citations=saved_citations,
            related_posts=[],
        )

    async def _prepare(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        embedding: list[float] | None,
    ) -> tuple[str | None, list[AssistantCitation], list[Turn], uuid.UUID | None]:
        knowledge_text: str | None = None
        citations: list[AssistantCitation] = []
        if embedding is not None:
            passing = await self._matching(embedding)
            if passing:
                knowledge_text = knowledge_answer(passing)
                citations = _citations_from_chunks(passing)
        existing_id: uuid.UUID | None = None
        prior: list[Turn] = []
        if conversation_id is not None:
            found = await self._conversations.get(conversation_id)
            if found is None or found.user_id != user_id:
                raise AppError(ErrorCode.NOT_FOUND, "Conversation not found", 404)
            existing_id = found.id
            prior = await self._conversations.prior_turns(found.id)
        return knowledge_text, citations, prior, existing_id

    async def _answer(
        self,
        question: str,
        *,
        refused: bool,
        knowledge_text: str | None,
        citations: list[AssistantCitation],
        prior: list[Turn],
    ) -> tuple[str, Literal["knowledge", "search", "generated"], list[AssistantCitation]]:
        if refused:
            return REFUSE_ANSWER, "generated", []
        if knowledge_text is not None:
            return knowledge_text, "knowledge", citations
        answer = await self._completer.complete(question, model_history(prior))
        return answer, "generated", []

    async def _matching(
        self,
        embedding: list[float],
    ) -> list[tuple[KnowledgeChunk, float]]:
        rows = await self._knowledge.similar_chunks(embedding, k=TOP_K)
        limit = 1 - get_settings().embedding_min_cosine
        return [(chunk, distance) for chunk, distance in rows if distance <= limit]
