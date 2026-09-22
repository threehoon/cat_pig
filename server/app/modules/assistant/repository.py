import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.assistant.models import KnowledgeArticle, KnowledgeChunk


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
            .order_by(distance.asc())
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
        embed_text: str,
        embedding: list[float],
        embedding_model: str,
    ) -> None:
        article = KnowledgeArticle(
            title=title,
            body=body,
            snippet=snippet,
            status="published",
            source_uri=source_uri,
            content_hash=content_hash,
            embedding_model=embedding_model,
        )
        self._session.add(article)
        await self._session.flush()
        await self.insert_chunk(
            article_id=article.id,
            embed_text=embed_text,
            embedding=embedding,
            embedding_model=embedding_model,
        )

    async def update_article(
        self,
        article: KnowledgeArticle,
        *,
        title: str,
        snippet: str,
        body: str,
        content_hash: str,
        embedding_model: str,
    ) -> None:
        article.title = title
        article.snippet = snippet
        article.body = body
        article.content_hash = content_hash
        article.embedding_model = embedding_model
        article.status = "published"
        await self._session.flush()

    async def delete_chunks(self, article_id: uuid.UUID) -> None:
        await self._session.execute(
            delete(KnowledgeChunk).where(KnowledgeChunk.article_id == article_id)
        )
        await self._session.flush()

    async def insert_chunk(
        self,
        *,
        article_id: uuid.UUID,
        embed_text: str,
        embedding: list[float],
        embedding_model: str,
    ) -> None:
        self._session.add(
            KnowledgeChunk(
                article_id=article_id,
                chunk_index=0,
                text=embed_text,
                embedding=embedding,
                embedding_model=embedding_model,
            )
        )
        await self._session.flush()
