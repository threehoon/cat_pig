from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionFactory
from app.core.settings import get_settings
from app.modules.assistant.embeddings import hash_embed
from app.modules.assistant.ingest import chunk_article, content_hash, ingest_directory
from app.modules.assistant.models import KnowledgeArticle, KnowledgeChunk

COOLING_TITLE = "夏天给狗降温"
COOLING_SNIPPET = "避开正午出门，室内通风，提供阴凉饮水和湿毛巾擦身，不要用冰水浇身。"
COOLING_BODY = (
    "夏天给狗降温，先避开正午出门，改在清晨或傍晚。屋里通风、留阴凉处，随时有干净凉水。"
    "可以用湿毛巾擦肚皮和脚垫散热，不要浇冰水、不要把狗关在停驶的车里。"
    "我是小x，这是说明书里的日常护理，不能代替兽医。"
)
SEED_DIR = Path(__file__).resolve().parents[3] / "app" / "modules" / "assistant" / "seed"
MARKER = "qx7marker-token-alpha-9012"
FILLER = "甲" * 420
ASK_TITLE = "标题"


def long_marker_body() -> str:
    return f"{MARKER}\n\n\n\n{FILLER}\n\n   \n\n{MARKER}"


def write_article(directory: Path, name: str, title: str, snippet: str, body: str) -> None:
    directory.joinpath(name).write_text(
        f"---\ntitle: {title}\nsnippet: {snippet}\n---\n\n{body}\n",
        encoding="utf-8",
    )


async def chunks_for(session: AsyncSession, source_uri: str) -> list[KnowledgeChunk]:
    rows = await session.scalars(
        select(KnowledgeChunk)
        .join(KnowledgeArticle)
        .where(KnowledgeArticle.source_uri == source_uri)
        .order_by(KnowledgeChunk.chunk_index.asc())
    )
    return list(rows)


async def chunk_ids_by_source(session: AsyncSession) -> dict[str, object]:
    rows = (
        await session.execute(
            select(KnowledgeArticle.source_uri, KnowledgeChunk.id).join(KnowledgeChunk)
        )
    ).all()
    return {source_uri: chunk_id for source_uri, chunk_id in rows}


async def test_ingest_skips_unchanged_files_and_replaces_changed_chunks(tmp_path: Path) -> None:
    write_article(tmp_path, "one.md", "One", "snippet one", "body one")
    write_article(tmp_path, "two.md", "Two", "snippet two", "body two")

    async with SessionFactory() as session:
        await ingest_directory(session, tmp_path)
        assert await session.scalar(select(func.count()).select_from(KnowledgeArticle)) == 2
        assert await session.scalar(select(func.count()).select_from(KnowledgeChunk)) == 2
        first_ids = await chunk_ids_by_source(session)

        await ingest_directory(session, tmp_path)
        assert await chunk_ids_by_source(session) == first_ids

        write_article(tmp_path, "one.md", "One", "snippet one", "body one changed")
        await ingest_directory(session, tmp_path)
        changed = (
            await session.execute(
                select(KnowledgeChunk)
                .join(KnowledgeArticle)
                .where(KnowledgeArticle.source_uri == "one.md")
            )
        ).scalars().all()
        assert len(changed) == 1
        assert changed[0].id != first_ids["one.md"]
        assert changed[0].text == "One\nbody one changed"
        assert (await chunk_ids_by_source(session))["two.md"] == first_ids["two.md"]

    async with SessionFactory() as other:
        assert await other.scalar(select(func.count()).select_from(KnowledgeArticle)) == 0


async def test_cooling_seed_matches_mock_wording() -> None:
    async with SessionFactory() as session:
        await ingest_directory(session, SEED_DIR)
        article = await session.scalar(
            select(KnowledgeArticle).where(
                KnowledgeArticle.source_uri == "summer-dog-cooling.md"
            )
        )
        assert article is not None
        assert article.title == COOLING_TITLE
        assert article.snippet == COOLING_SNIPPET
        assert article.body == COOLING_BODY
        assert article.status == "published"

        chunk = await session.scalar(
            select(KnowledgeChunk).where(KnowledgeChunk.article_id == article.id)
        )
        assert chunk is not None
        assert chunk.chunk_index == 0
        assert chunk.text == f"{COOLING_TITLE}\n{COOLING_BODY}"


async def test_long_body_drops_empty_segments_and_numbers_chunks(tmp_path: Path) -> None:
    body = long_marker_body()
    write_article(tmp_path, "long.md", ASK_TITLE, "长文摘要", body)
    normalized, texts = chunk_article(ASK_TITLE, body)

    async with SessionFactory() as session:
        await ingest_directory(session, tmp_path)
        article = await session.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.source_uri == "long.md")
        )
        chunks = await chunks_for(session, "long.md")

    assert article is not None
    assert article.body == normalized
    assert [chunk.chunk_index for chunk in chunks] == [0, 1, 2]
    assert [chunk.text for chunk in chunks] == texts
    assert [chunk.text.split("\n", 1)[0] for chunk in chunks] == [ASK_TITLE, ASK_TITLE, ASK_TITLE]
    assert [chunk.text.split("\n", 1)[1] for chunk in chunks] == [MARKER, FILLER, MARKER]


async def test_overlong_paragraph_stays_one_chunk(tmp_path: Path) -> None:
    body = "甲" * 401
    write_article(tmp_path, "wide.md", ASK_TITLE, "一段", body)

    async with SessionFactory() as session:
        await ingest_directory(session, tmp_path)
        article = await session.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.source_uri == "wide.md")
        )
        chunks = await chunks_for(session, "wide.md")

    assert article is not None
    assert article.body == body
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == f"{ASK_TITLE}\n{body}"


async def test_crlf_in_body_is_normalized_before_hash_and_chunks(tmp_path: Path) -> None:
    raw = "甲\r\n乙"
    write_article(tmp_path, "crlf.md", ASK_TITLE, "换行", raw)
    normalized, texts = chunk_article(ASK_TITLE, raw)

    async with SessionFactory() as session:
        await ingest_directory(session, tmp_path)
        article = await session.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.source_uri == "crlf.md")
        )
        chunks = await chunks_for(session, "crlf.md")

    assert article is not None
    assert normalized == "甲\n乙"
    assert article.body == normalized
    assert article.content_hash == content_hash(ASK_TITLE, "换行", normalized)
    assert article.content_hash != content_hash(ASK_TITLE, "换行", raw)
    assert [chunk.text for chunk in chunks] == texts


async def test_changed_model_name_rewrites_chunks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EMBEDDING_BASE_URL", "")
    monkeypatch.setenv("EMBEDDING_API_KEY", "")
    monkeypatch.setenv("EMBEDDING_MODEL", "")
    get_settings.cache_clear()
    write_article(tmp_path, "one.md", "One", "snippet one", "body one")

    async with SessionFactory() as session:
        await ingest_directory(session, tmp_path)
        article = await session.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.source_uri == "one.md")
        )
        assert article is not None
        assert article.embedding_model == "hash"
        first_ids = [chunk.id for chunk in await chunks_for(session, "one.md")]
        article.embedding_model = "other-model"
        await session.flush()

        await ingest_directory(session, tmp_path)
        await session.refresh(article)
        rewritten = await chunks_for(session, "one.md")

    assert article.embedding_model == "hash"
    assert [chunk.id for chunk in rewritten] != first_ids
    assert len(rewritten) == 1
    assert rewritten[0].text == "One\nbody one"


async def test_short_body_stored_as_two_chunks_is_rewritten(tmp_path: Path) -> None:
    write_article(tmp_path, "one.md", "One", "snippet one", "body one")

    async with SessionFactory() as session:
        await ingest_directory(session, tmp_path)
        article = await session.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.source_uri == "one.md")
        )
        assert article is not None
        stored = await chunks_for(session, "one.md")
        for chunk in stored:
            await session.delete(chunk)
        await session.flush()
        session.add_all(
            [
                KnowledgeChunk(
                    article_id=article.id,
                    chunk_index=0,
                    text="One\nleft",
                    embedding=hash_embed("left", 1024),
                    embedding_model=article.embedding_model,
                ),
                KnowledgeChunk(
                    article_id=article.id,
                    chunk_index=1,
                    text="One\nright",
                    embedding=hash_embed("right", 1024),
                    embedding_model=article.embedding_model,
                ),
            ]
        )
        await session.flush()
        stale_ids = [chunk.id for chunk in await chunks_for(session, "one.md")]

        await ingest_directory(session, tmp_path)
        rewritten = await chunks_for(session, "one.md")

    assert len(stale_ids) == 2
    assert [chunk.chunk_index for chunk in rewritten] == [0]
    assert rewritten[0].text == "One\nbody one"
    assert rewritten[0].id not in stale_ids


async def test_long_body_stored_as_one_chunk_is_rewritten(tmp_path: Path) -> None:
    body = long_marker_body()
    write_article(tmp_path, "long.md", ASK_TITLE, "长文摘要", body)
    _normalized, texts = chunk_article(ASK_TITLE, body)

    async with SessionFactory() as session:
        await ingest_directory(session, tmp_path)
        article = await session.scalar(
            select(KnowledgeArticle).where(KnowledgeArticle.source_uri == "long.md")
        )
        assert article is not None
        stored = await chunks_for(session, "long.md")
        for chunk in stored:
            await session.delete(chunk)
        await session.flush()
        stale = KnowledgeChunk(
            article_id=article.id,
            chunk_index=0,
            text=f"{ASK_TITLE}\n{body}",
            embedding=hash_embed("stale", 1024),
            embedding_model=article.embedding_model,
        )
        session.add(stale)
        await session.flush()

        await ingest_directory(session, tmp_path)
        rewritten = await chunks_for(session, "long.md")

    assert [chunk.text for chunk in rewritten] == texts
    assert stale.id not in [chunk.id for chunk in rewritten]
