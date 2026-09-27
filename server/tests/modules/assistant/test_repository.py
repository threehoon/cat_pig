import uuid

from app.core.db import SessionFactory
from app.modules.assistant.embeddings import hash_embed
from app.modules.assistant.models import KnowledgeArticle, KnowledgeChunk
from app.modules.assistant.repository import KnowledgeRepository

ALPHA = "alpha-unique-token-xyz"
OTHER = "totally-different-zzz"


def make_article(source_uri: str, status: str, title: str) -> KnowledgeArticle:
    return KnowledgeArticle(
        title=title,
        body="body",
        snippet="snippet",
        status=status,
        source_uri=source_uri,
        content_hash=source_uri,
        embedding_model="hash",
    )


async def test_same_vector_is_near_zero_and_loads_article() -> None:
    embedding = hash_embed(ALPHA, 1024)
    async with SessionFactory() as session:
        article = make_article("alpha.md", "published", "Alpha title")
        session.add(article)
        await session.flush()
        session.add(
            KnowledgeChunk(
                article_id=article.id,
                chunk_index=0,
                text=ALPHA,
                embedding=embedding,
                embedding_model="hash",
            )
        )
        await session.flush()

        rows = await KnowledgeRepository(session).similar_chunks(embedding)
        chunk, distance = rows[0]

        assert distance < 1e-6
        assert chunk.article.title == "Alpha title"


async def test_different_vector_stays_far_when_row_is_returned() -> None:
    embedding = hash_embed(ALPHA, 1024)
    other = hash_embed(OTHER, 1024)
    async with SessionFactory() as session:
        article = make_article("alpha.md", "published", "Alpha title")
        session.add(article)
        await session.flush()
        session.add(
            KnowledgeChunk(
                article_id=article.id,
                chunk_index=0,
                text=ALPHA,
                embedding=embedding,
                embedding_model="hash",
            )
        )
        await session.flush()

        rows = await KnowledgeRepository(session).similar_chunks(other)
        matched = [row for row in rows if row[0].article_id == article.id]
        if matched:
            assert matched[0][1] > 0.5


async def test_archived_article_is_left_out_of_similar_chunks() -> None:
    embedding = hash_embed(ALPHA, 1024)
    async with SessionFactory() as session:
        published = make_article("alpha.md", "published", "Alpha title")
        archived = make_article("archived.md", "archived", "Archived title")
        session.add_all([published, archived])
        await session.flush()
        session.add_all(
            [
                KnowledgeChunk(
                    article_id=published.id,
                    chunk_index=0,
                    text=ALPHA,
                    embedding=embedding,
                    embedding_model="hash",
                ),
                KnowledgeChunk(
                    article_id=archived.id,
                    chunk_index=0,
                    text=ALPHA,
                    embedding=embedding,
                    embedding_model="hash",
                ),
            ]
        )
        await session.flush()

        rows = await KnowledgeRepository(session).similar_chunks(embedding)
        article_ids = {chunk.article_id for chunk, _distance in rows}

        assert published.id in article_ids
        assert archived.id not in article_ids


async def test_similar_chunks_orders_ties_by_index_then_id() -> None:
    embedding = hash_embed(ALPHA, 1024)
    low_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    high_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    async with SessionFactory() as session:
        first = make_article("first.md", "published", "First")
        second = make_article("second.md", "published", "Second")
        session.add_all([first, second])
        await session.flush()
        later = KnowledgeChunk(
            article_id=first.id,
            chunk_index=1,
            text=ALPHA,
            embedding=embedding,
            embedding_model="hash",
        )
        session.add_all(
            [
                KnowledgeChunk(
                    id=low_id,
                    article_id=first.id,
                    chunk_index=0,
                    text=ALPHA,
                    embedding=embedding,
                    embedding_model="hash",
                ),
                KnowledgeChunk(
                    id=high_id,
                    article_id=second.id,
                    chunk_index=0,
                    text=ALPHA,
                    embedding=embedding,
                    embedding_model="hash",
                ),
                later,
            ]
        )
        await session.flush()

        rows = await KnowledgeRepository(session).similar_chunks(embedding)

    assert [chunk.id for chunk, _distance in rows] == [low_id, high_id, later.id]
    assert [chunk.chunk_index for chunk, _distance in rows] == [0, 0, 1]
