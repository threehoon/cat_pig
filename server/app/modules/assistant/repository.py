import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.clock import now_utc
from app.modules.assistant.completion import Turn
from app.modules.assistant.models import (
    Conversation,
    ConversationMessage,
    KnowledgeArticle,
    KnowledgeChunk,
)


class KnowledgeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def similar_chunks(
        self,
        embedding: list[float],
        k: int = 8,
    ) -> list[tuple[KnowledgeChunk, float]]:
        distance = KnowledgeChunk.embedding.cosine_distance(embedding)
        statement = (
            select(KnowledgeChunk, distance)
            .where(KnowledgeChunk.article.has(KnowledgeArticle.status == "published"))
            .options(joinedload(KnowledgeChunk.article))
            .order_by(
                distance.asc(),
                KnowledgeChunk.chunk_index.asc(),
                KnowledgeChunk.id.asc(),
            )
            .limit(k)
        )
        rows = (await self._session.execute(statement)).unique().all()
        return [(chunk, float(dist)) for chunk, dist in rows]

    async def find_by_source_uri(self, source_uri: str) -> KnowledgeArticle | None:
        return await self._session.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.source_uri == source_uri)
        )

    async def insert_published(
        self,
        *,
        source_uri: str,
        title: str,
        snippet: str,
        body: str,
        content_hash: str,
    ) -> KnowledgeArticle:
        article = KnowledgeArticle(
            title=title,
            body=body,
            snippet=snippet,
            status="published",
            source_uri=source_uri,
            content_hash=content_hash,
            embedding_model="",
        )
        self._session.add(article)
        await self._session.flush()
        return article

    async def update_article(
        self,
        article: KnowledgeArticle,
        *,
        title: str,
        snippet: str,
        body: str,
        content_hash: str,
    ) -> None:
        article.title = title
        article.snippet = snippet
        article.body = body
        article.content_hash = content_hash
        article.status = "published"
        await self._session.flush()

    async def set_embedding_model(self, article: KnowledgeArticle, embedding_model: str) -> None:
        article.embedding_model = embedding_model
        await self._session.flush()

    async def delete_chunks(self, article_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.article_id == article_id)
        )
        await self._session.flush()

    async def list_chunks(self, article_id: uuid.UUID) -> list[KnowledgeChunk]:
        rows = await self._session.scalars(
            select(KnowledgeChunk)
            .where(KnowledgeChunk.article_id == article_id)
            .order_by(KnowledgeChunk.chunk_index.asc())
        )
        return list(rows)

    async def insert_chunk(
        self,
        *,
        article_id: uuid.UUID,
        chunk_index: int,
        embed_text: str,
        embedding: list[float],
        embedding_model: str,
    ) -> None:
        self._session.add(
            KnowledgeChunk(
                article_id=article_id,
                chunk_index=chunk_index,
                text=embed_text,
                embedding=embedding,
                embedding_model=embedding_model,
            )
        )
        await self._session.flush()


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        if self._session.in_transaction():
            await self._session.commit()

    async def get(self, conversation_id: uuid.UUID) -> Conversation | None:
        return await self._session.get(Conversation, conversation_id)

    async def prior_turns(self, conversation_id: uuid.UUID) -> list[Turn]:
        rows = await self._session.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.seq.asc())
        )
        return [Turn(row.role, row.body) for row in rows]

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[Conversation], int]:
        has_message = (
            select(ConversationMessage.id)
            .where(ConversationMessage.conversation_id == Conversation.id)
            .exists()
        )
        filters = (Conversation.user_id == user_id, has_message)
        total = await self._session.scalar(
            select(func.count()).select_from(Conversation).where(*filters)
        )
        statement = (
            select(Conversation)
            .where(*filters)
            .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(await self._session.scalars(statement))
        return rows, int(total or 0)

    async def list_messages(
        self,
        conversation_id: uuid.UUID,
        page: int,
        page_size: int,
    ) -> tuple[list[ConversationMessage], int]:
        filters = (ConversationMessage.conversation_id == conversation_id,)
        total = await self._session.scalar(
            select(func.count()).select_from(ConversationMessage).where(*filters)
        )
        statement = (
            select(ConversationMessage)
            .where(*filters)
            .order_by(ConversationMessage.seq.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = list(await self._session.scalars(statement))
        return rows, int(total or 0)

    async def append_exchange(
        self,
        *,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID | None,
        question: str,
        answer: str,
        source: str,
        citations: list[dict[str, str]],
    ) -> uuid.UUID | None:
        if conversation_id is None:
            conversation = Conversation(user_id=user_id, title=question, updated_at=now_utc())
            self._session.add(conversation)
            await self._session.flush()
            next_seq = 1
        else:
            conversation = await self._session.get(Conversation, conversation_id)
            if conversation is None or conversation.user_id != user_id:
                return None
            if conversation.title is None:
                conversation.title = question
            conversation.updated_at = now_utc()
            current = await self._session.scalar(
                select(func.max(ConversationMessage.seq)).where(
                    ConversationMessage.conversation_id == conversation.id
                )
            )
            next_seq = int(current or 0) + 1
        self._session.add(
            ConversationMessage(
                conversation_id=conversation.id,
                seq=next_seq,
                role="user",
                body=question,
                source=None,
                citations=[],
            )
        )
        self._session.add(
            ConversationMessage(
                conversation_id=conversation.id,
                seq=next_seq + 1,
                role="assistant",
                body=answer,
                source=source,
                citations=citations,
            )
        )
        await self._session.flush()
        return conversation.id
