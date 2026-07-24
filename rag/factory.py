from __future__ import annotations

from core.config import AppConfig

from .embeddings import create_embedding_provider
from .retriever import VectorRetriever
from .vector_store import SQLiteVectorStore


def build_components(config: AppConfig):
    embeddings = create_embedding_provider(config.rag.embedding_provider, config.rag.embedding_model)
    if config.rag.vector_backend != "sqlite":
        raise ValueError(f"Unsupported vector backend: {config.rag.vector_backend}")
    store = SQLiteVectorStore(config.rag.vector_store_path, embeddings.dimension)
    return embeddings, store


def build_retriever(config: AppConfig) -> VectorRetriever:
    embeddings, store = build_components(config)
    return VectorRetriever(embeddings, store, config.rag.top_k)
