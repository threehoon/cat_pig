import asyncio
import hashlib
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import SessionFactory
from app.modules.assistant.embeddings import HttpEmbedder, get_embedder
from app.modules.assistant.models import KnowledgeArticle
from app.modules.assistant.repository import KnowledgeRepository

SEED_DIR = Path(__file__).parent / "seed"
_FRONTMATTER_END = "\n---\n"


def content_hash(title: str, snippet: str, body: str) -> str:
    payload = f"{title}|{snippet}|{body}"
    return hashlib.sha256(payload.encode()).hexdigest()


def chunk_article(title: str, body: str) -> tuple[str, list[str]]:
    normalized = body.replace("\r\n", "\n")
    if len(normalized) <= 400:
        segments = [normalized]
    else:
        segments = [part.strip() for part in normalized.split("\n\n")]
        segments = [part for part in segments if part]
    return normalized, [f"{title}\n{segment}" for segment in segments]


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


async def _chunks_match(
    repository: KnowledgeRepository,
    article: KnowledgeArticle,
    digest: str,
    model_name: str,
    texts: list[str],
) -> bool:
    if article.content_hash != digest or article.embedding_model != model_name:
        return False
    stored = await repository.list_chunks(article.id)
    return [chunk.text for chunk in stored] == texts


async def ingest_directory(session: AsyncSession, directory: Path) -> None:
    repository = KnowledgeRepository(session)
    embedder = get_embedder()
    model_name = embedder.model if isinstance(embedder, HttpEmbedder) else "hash"
    for path in sorted(directory.glob("*.md")):
        title, snippet, raw_body = parse_article(path.read_text(encoding="utf-8"))
        normalized, texts = chunk_article(title, raw_body)
        digest = content_hash(title, snippet, normalized)
        existing = await repository.find_by_source_uri(path.name)
        if existing is not None and await _chunks_match(
            repository,
            existing,
            digest,
            model_name,
            texts,
        ):
            continue
        embeddings = [await embedder.embed(text) for text in texts]
        if existing is None:
            article = await repository.insert_published(
                source_uri=path.name,
                title=title,
                snippet=snippet,
                body=normalized,
                content_hash=digest,
            )
        else:
            await repository.update_article(
                existing,
                title=title,
                snippet=snippet,
                body=normalized,
                content_hash=digest,
            )
            await repository.delete_chunks(existing.id)
            article = existing
        for index, (text, embedding) in enumerate(zip(texts, embeddings, strict=True)):
            await repository.insert_chunk(
                article_id=article.id,
                chunk_index=index,
                embed_text=text,
                embedding=embedding,
                embedding_model=model_name,
            )
        await repository.set_embedding_model(article, model_name)


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
