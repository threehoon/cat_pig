import uuid

from app.core.exceptions import AppError, ErrorCode
from app.core.pagination import PageQuery
from app.core.settings import get_settings
from app.modules.assistant.completion import Completer
from app.modules.assistant.embeddings import Embedder
from app.modules.assistant.models import Conversation, KnowledgeChunk
from app.modules.assistant.repository import ConversationRepository, KnowledgeRepository
from app.modules.assistant.schemas import (
    AssistantAsk,
    AssistantCitation,
    AssistantSuggestion,
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

    async def ask(
        self,
        user_id: uuid.UUID,
        question: str,
        conversation_id: uuid.UUID | None,
    ) -> AssistantAsk:
        stripped = question.strip()
        if not stripped:
            raise AppError(ErrorCode.VALIDATION, "Question is required", 400)

        conversation = await self._conversation_for(user_id, conversation_id)
        if any(word in stripped for word in REFUSE_WORDS):
            return self._generated(conversation, REFUSE_ANSWER)

        passing = await self.passing_chunks(stripped)
        if not passing:
            answer = await self._completer.complete(stripped)
            return self._generated(conversation, answer)

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
        return AssistantAsk(
            conversation_id=str(conversation.id),
            answer=knowledge_answer(passing),
            source="knowledge",
            citations=citations,
            related_posts=[],
        )

    async def passing_chunks(
        self,
        question: str,
    ) -> list[tuple[KnowledgeChunk, float]]:
        embedding = await self._embedder.embed(question)
        rows = await self._knowledge.similar_chunks(embedding, k=TOP_K)
        limit = 1 - get_settings().embedding_min_cosine
        return [(chunk, distance) for chunk, distance in rows if distance <= limit]

    async def _conversation_for(
        self,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
    ) -> Conversation:
        if conversation_id is None:
            return await self._conversations.add(user_id)
        found = await self._conversations.get(conversation_id)
        if found is None or found.user_id != user_id:
            raise AppError(ErrorCode.NOT_FOUND, "Conversation not found", 404)
        return found

    def _generated(self, conversation: Conversation, answer: str) -> AssistantAsk:
        return AssistantAsk(
            conversation_id=str(conversation.id),
            answer=answer,
            source="generated",
            citations=[],
            related_posts=[],
        )
