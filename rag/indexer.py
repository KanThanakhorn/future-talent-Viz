from __future__ import annotations

import logging
import time
from collections.abc import Iterable

from core.interfaces import DocumentLoader, EmbeddingProvider, VectorStore
from core.models import DocumentChunk

LOG = logging.getLogger(__name__)


class DocumentIndexer:
    def __init__(self, loader: DocumentLoader, embeddings: EmbeddingProvider, store: VectorStore, batch_size: int = 64) -> None:
        self.loader = loader
        self.embeddings = embeddings
        self.store = store
        self.batch_size = batch_size

    def index(self, paths: Iterable[str]) -> int:
        chunks = list(self.loader.load(paths))
        self.store.delete_documents([chunk.metadata.document_id for chunk in chunks])
        for offset in range(0, len(chunks), self.batch_size):
            batch: list[DocumentChunk] = chunks[offset : offset + self.batch_size]
            started = time.perf_counter()
            vectors = self.embeddings.embed_documents([chunk.text for chunk in batch])
            LOG.info("embedding_complete", extra={
                "event": "embedding_complete",
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                "result_count": len(batch),
            })
            self.store.upsert(batch, vectors)
        return len(chunks)
