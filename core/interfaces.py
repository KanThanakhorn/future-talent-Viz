from __future__ import annotations

from typing import Any, Iterable, Protocol, Sequence

from .models import DocumentChunk, Generation, RetrievedChunk, ToolEvidence


class DocumentLoader(Protocol):
    def load(self, paths: Iterable[str]) -> Iterable[DocumentChunk]: ...


class Chunker(Protocol):
    def split(self, document_id: str, pages: Sequence[tuple[int, str]], source_filename: str) -> list[DocumentChunk]: ...


class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...

    def embed_query(self, text: str) -> list[float]: ...


class VectorStore(Protocol):
    def delete_documents(self, document_ids: Sequence[str]) -> None: ...

    def upsert(self, chunks: Sequence[DocumentChunk], vectors: Sequence[Sequence[float]]) -> None: ...

    def search(self, vector: Sequence[float], top_k: int) -> list[RetrievedChunk]: ...


class Retriever(Protocol):
    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievedChunk]: ...


class LLMProvider(Protocol):
    def generate(
        self, prompt: str, *, model: str | None = None, reasoning_effort: str | None = None
    ) -> Generation: ...


class SQLToolClient(Protocol):
    def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolEvidence: ...
