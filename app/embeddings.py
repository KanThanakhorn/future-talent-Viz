from __future__ import annotations

import logging
from functools import lru_cache

from .config import settings

LOG = logging.getLogger(__name__)


class ModelUnavailable(RuntimeError):
    pass


@lru_cache(maxsize=1)
def text_model():
    try:
        from fastembed import TextEmbedding
    except ImportError as exc:
        raise ModelUnavailable("fastembed is not installed; run scripts/setup-local.sh") from exc
    settings.model_cache_path.mkdir(parents=True, exist_ok=True)
    return TextEmbedding(model_name=settings.embedding_model, cache_dir=str(settings.model_cache_path))


def embed_passages(texts: list[str]) -> list[list[float]]:
    return [vector.astype(float).tolist() for vector in text_model().embed(texts)]


def embed_query(text: str) -> list[float]:
    return embed_passages([text])[0]


@lru_cache(maxsize=1)
def cross_encoder():
    try:
        from fastembed.rerank.cross_encoder import TextCrossEncoder
    except ImportError as exc:
        raise ModelUnavailable("fastembed reranker is not installed") from exc
    settings.model_cache_path.mkdir(parents=True, exist_ok=True)
    return TextCrossEncoder(model_name=settings.reranker_model, cache_dir=str(settings.model_cache_path))


def rerank(query: str, documents: list[str]) -> list[float]:
    return [float(score) for score in cross_encoder().rerank(query, documents)]
