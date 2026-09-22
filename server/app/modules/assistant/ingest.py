import asyncio
import hashlib
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionFactory
from app.modules.assistant.embeddings import HttpEmbedder, get_embedder
from app.modules.assistant.repository import KnowledgeRepository

SEED_DIR = Path(__file__).parent / "seed"
_FRONTMATTER_END = "\n---\n"


def content_hash(title: str, snippet: str, body: str) -> str:
    payload = f"{title}|{snippet}|{body}"
    return hashlib.sha256(payload.encode()).hexdigest()


def parse_article(raw: str) -> tuple[str, str, str]:
    if not raw.startswith("---\n"):
        raise ValueError("seed file is missing opening frontmatter")
    rest = raw[4:]
    end = rest.find(_FRONTMATTER_END)
    if end < 0:
        raise ValueError("seed file is missing closing frontmatter")
    title: str | None = None
    snippet: str | None = None
    for line in rest[:end].splitlines():
        if line.startswith("title:"):
            title = line.removeprefix("title:").strip()
        elif line.startswith("snippet:"):
            snippet = line.removeprefix("snippet:").strip()
    if not title or snippet is None:
        raise ValueError("seed frontmatter needs title and snippet")
    body = rest[end + len(_FRONTMATTER_END) :].strip("\n")
    return title, snippet, body


async def ingest_directory(session: AsyncSession, directory: Path) -> None:
    repository = KnowledgeRepository(session)
    embedder = get_embedder()
    model_name = embedder.model if isinstance(embedder, HttpEmbedder) else "hash"
    for path in sorted(directory.glob("*.md")):
        title, snippet, body = parse_article(path.read_text(encoding="utf-8"))
        digest = content_hash(title, snippet, body)
        existing = await repository.find_by_source_uri(path.name)
        if existing is not None and existing.content_hash == digest:
            continue
        embed_text = f"{title}\n{body}"
        if existing is None:
            embedding = await embedder.embed(embed_text)
            await repository.insert_published(
                source_uri=path.name,
                title=title,
                snippet=snippet,
                body=body,
                content_hash=digest,
                embed_text=embed_text,
                embedding=embedding,
                embedding_model=model_name,
            )
            continue
        await repository.update_article(
            existing,
            title=title,
            snippet=snippet,
            body=body,
            content_hash=digest,
            embedding_model=model_name,
        )
        await repository.delete_chunks(existing.id)
        embedding = await embedder.embed(embed_text)
        await repository.insert_chunk(
            article_id=existing.id,
            embed_text=embed_text,
            embedding=embedding,
            embedding_model=model_name,
        )


async def _main() -> None:
    async with SessionFactory() as session:
        try:
            await ingest_directory(session, SEED_DIR)
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
