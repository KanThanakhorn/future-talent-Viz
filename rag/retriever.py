from __future__ import annotations

import logging
import time

from core.interfaces import EmbeddingProvider, VectorStore
from core.models import RetrievedChunk

LOG = logging.getLogger(__name__)


class VectorRetriever:
    def __init__(self, embeddings: EmbeddingProvider, store: VectorStore, top_k: int = 6) -> None:
        self.embeddings = embeddings
        self.store = store
        self.top_k = top_k

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
        started = time.perf_counter()
        vector = self.embeddings.embed_query(question)
        embedding_ms = (time.perf_counter() - started) * 1000
        results = self.store.search(vector, top_k or self.top_k)
        total_ms = (time.perf_counter() - started) * 1000
        LOG.info("retrieval_complete", extra={
            "event": "retrieval_complete", "duration_ms": round(total_ms, 2),
            "result_count": len(results), "question_length": len(question),
        })
        LOG.info("query_embedding_complete", extra={"event": "query_embedding_complete", "duration_ms": round(embedding_ms, 2)})
        return results
