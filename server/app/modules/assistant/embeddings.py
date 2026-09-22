import hashlib
import math
import re
from typing import Protocol

import httpx

from app.core.settings import get_settings

_WHITESPACE = re.compile(r"\s+")


def hash_embed(text: str, dim: int) -> list[float]:
    vector = [0.0] * dim
    compact = _WHITESPACE.sub("", text)
    for n in (2, 3):
        grams = [compact[i : i + n] for i in range(max(len(compact) - n + 1, 0))]
        if not grams and compact:
            grams = [compact]
        for gram in grams:
            digest = hashlib.sha256(f"{n}:{gram}".encode()).digest()
            index = int.from_bytes(digest[:8], "big") % dim
            sign = 1.0 if digest[8] % 2 == 0 else -1.0
            vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


class Embedder(Protocol):
    async def embed(self, text: str) -> list[float]: ...


class HashEmbedder:
    def __init__(self, dim: int) -> None:
        self.dim = dim

    async def embed(self, text: str) -> list[float]:
        return hash_embed(text, self.dim)


class HttpEmbedder:
    def __init__(self, base_url: str, api_key: str, model: str, dim: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.dim = dim

    async def embed(self, text: str) -> list[float]:
        url = f"{self.base_url}/embeddings"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json={"model": self.model, "input": text},
            )
        response.raise_for_status()
        vector = response.json()["data"][0]["embedding"]
        if len(vector) != self.dim:
            raise RuntimeError(
                f"embedding dim mismatch: expected {self.dim}, got {len(vector)}"
            )
        return [float(value) for value in vector]


def get_embedder() -> Embedder:
    settings = get_settings()
    if settings.embedding_api_key and settings.embedding_base_url and settings.embedding_model:
        return HttpEmbedder(
            settings.embedding_base_url,
            settings.embedding_api_key,
            settings.embedding_model,
            settings.embedding_dim,
        )
    return HashEmbedder(settings.embedding_dim)
