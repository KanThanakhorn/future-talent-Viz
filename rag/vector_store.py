from __future__ import annotations

import json
import math
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from core.models import ChunkMetadata, DocumentChunk, RetrievedChunk


class SQLiteVectorStore:
    """Local exact-search vector store. The interface can be replaced by Chroma/FAISS."""

    def __init__(self, path: Path, dimension: int) -> None:
        self.path = path
        self.dimension = dimension
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS vectors (
                   chunk_id TEXT PRIMARY KEY, text TEXT NOT NULL, vector TEXT NOT NULL,
                   document_id TEXT NOT NULL, page_number INTEGER, section TEXT,
                   source_filename TEXT NOT NULL, source_type TEXT NOT NULL,
                   dimension INTEGER NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=10)

    def delete_documents(self, document_ids: Sequence[str]) -> None:
        values = list(dict.fromkeys(document_ids))
        if not values:
            return
        placeholders = ",".join("?" for _ in values)
        with self._connect() as conn:
            conn.execute(f"DELETE FROM vectors WHERE document_id IN ({placeholders})", values)

    def upsert(self, chunks: Sequence[DocumentChunk], vectors: Sequence[Sequence[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have equal length")
        rows = []
        for chunk, vector in zip(chunks, vectors):
            if len(vector) != self.dimension:
                raise ValueError(f"Expected vector dimension {self.dimension}, got {len(vector)}")
            metadata = chunk.metadata
            rows.append(
                (
                    chunk.chunk_id, chunk.text, json.dumps(list(vector)), metadata.document_id,
                    metadata.page_number, metadata.section, metadata.source_filename,
                    metadata.source_type, self.dimension,
                )
            )
        with self._connect() as conn:
            conn.executemany(
                """INSERT INTO vectors(chunk_id,text,vector,document_id,page_number,section,
                   source_filename,source_type,dimension) VALUES(?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(chunk_id) DO UPDATE SET text=excluded.text,vector=excluded.vector,
                   document_id=excluded.document_id,page_number=excluded.page_number,
                   section=excluded.section,source_filename=excluded.source_filename,
                   source_type=excluded.source_type,dimension=excluded.dimension,
                   updated_at=CURRENT_TIMESTAMP""",
                rows,
            )

    @staticmethod
    def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
        dot = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left)) or 1.0
        right_norm = math.sqrt(sum(value * value for value in right)) or 1.0
        return dot / (left_norm * right_norm)

    def search(self, vector: Sequence[float], top_k: int) -> list[RetrievedChunk]:
        if len(vector) != self.dimension:
            raise ValueError(f"Expected query dimension {self.dimension}, got {len(vector)}")
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT chunk_id,text,vector,document_id,page_number,section,
                          source_filename,source_type FROM vectors WHERE dimension=?""",
                (self.dimension,),
            ).fetchall()
        ranked = sorted(rows, key=lambda row: self._cosine(vector, json.loads(row[2])), reverse=True)
        return [
            RetrievedChunk(
                chunk=DocumentChunk(
                    chunk_id=row[0],
                    text=row[1],
                    metadata=ChunkMetadata(
                        document_id=row[3],
                        page_number=row[4],
                        section=row[5],
                        source_filename=row[6],
                        source_type=row[7],
                    ),
                ),
                score=self._cosine(vector, json.loads(row[2])),
            )
            for row in ranked[:top_k]
        ]

    def count(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM vectors").fetchone()[0])
