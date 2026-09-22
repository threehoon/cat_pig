from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionFactory
from app.modules.assistant.ingest import ingest_directory
from app.modules.assistant.models import KnowledgeArticle, KnowledgeChunk

COOLING_TITLE = "夏天给狗降温"
COOLING_SNIPPET = "避开正午出门，室内通风，提供阴凉饮水和湿毛巾擦身，不要用冰水浇身。"
COOLING_BODY = (
    "夏天给狗降温，先避开正午出门，改在清晨或傍晚。屋里通风、留阴凉处，随时有干净凉水。"
    "可以用湿毛巾擦肚皮和脚垫散热，不要浇冰水、不要把狗关在停驶的车里。"
    "我是小x，这是说明书里的日常护理，不能代替兽医。"
)
SEED_DIR = Path(__file__).resolve().parents[3] / "app" / "modules" / "assistant" / "seed"


def write_article(directory: Path, name: str, title: str, snippet: str, body: str) -> None:
    directory.joinpath(name).write_text(
        f"---\ntitle: {title}\nsnippet: {snippet}\n---\n\n{body}\n",
        encoding="utf-8",
    )


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
