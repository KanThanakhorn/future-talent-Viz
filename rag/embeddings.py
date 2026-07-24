from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from collections.abc import Sequence


class HashEmbeddingProvider:
    """Dependency-free deterministic fallback suitable for tests and offline use."""

    def __init__(self, dimension: int = 384) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def _embed(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-z0-9+#.-]+|[\u0e00-\u0e7f]+", text.lower())
        vector = [0.0] * self.dimension
        for token, count in Counter(tokens).items():
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            position = int.from_bytes(digest[:4], "big") % self.dimension
            vector[position] += (-1.0 if digest[4] & 1 else 1.0) * (1.0 + math.log(count))
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


class FastEmbedProvider:
    def __init__(self, model_name: str, cache_dir: str | None = None) -> None:
        from fastembed import TextEmbedding

        self.model = TextEmbedding(model_name=model_name, cache_dir=cache_dir)
        probe = list(self.model.embed(["dimension probe"]))[0]
        self._dimension = len(probe)

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [vector.tolist() for vector in self.model.embed(list(texts))]

    def embed_query(self, text: str) -> list[float]:
        return list(self.embed_documents([text])[0])


def create_embedding_provider(provider: str, model: str):
    if provider == "hash":
        return HashEmbeddingProvider()
    if provider == "fastembed":
        try:
            return FastEmbedProvider(model)
        except Exception:
            return HashEmbeddingProvider()
    raise ValueError(f"Unsupported embedding provider: {provider}")
