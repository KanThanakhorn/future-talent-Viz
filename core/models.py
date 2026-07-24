from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Route(str, Enum):
    RAG = "rag"
    SQL = "sql"
    HYBRID = "hybrid"


@dataclass(frozen=True)
class ChunkMetadata:
    document_id: str
    page_number: int | None
    section: str | None
    source_filename: str
    source_type: str = "pdf"


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    text: str
    metadata: ChunkMetadata


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


@dataclass(frozen=True)
class ToolEvidence:
    tool_name: str
    rows: list[dict[str, Any]]
    query: str | None = None


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


@dataclass(frozen=True)
class Generation:
    text: str
    model: str
    usage: Usage = field(default_factory=Usage)


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    evidence: list[str]
    chunks: list[RetrievedChunk]
    sql_evidence: list[ToolEvidence]
    route: Route
    model: str
    execution_time: float
    timings: dict[str, float]
    usage: Usage = field(default_factory=Usage)

