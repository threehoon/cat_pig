import uuid

from app.core.exceptions import AppError, ErrorCode
from app.core.pagination import PageQuery
from app.core.settings import get_settings
from app.modules.assistant.embeddings import Embedder
from app.modules.assistant.models import Conversation
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


class AssistantService:
    def __init__(
        self,
        knowledge: KnowledgeRepository,
        conversations: ConversationRepository,
        embedder: Embedder,
    ) -> None:
        self._knowledge = knowledge
        self._conversations = conversations
        self._embedder = embedder

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

        embedding = await self._embedder.embed(stripped)
        rows = await self._knowledge.similar_chunks(embedding, k=TOP_K)
        limit = 1 - get_settings().embedding_min_cosine
        passing = [(chunk, distance) for chunk, distance in rows if distance <= limit]
        if not passing:
            return self._generated(conversation, GENERATED_ANSWER)

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
            answer=passing[0][0].article.body,
            source="knowledge",
            citations=citations,
            related_posts=[],
        )

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
