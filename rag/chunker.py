from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence

from core.models import ChunkMetadata, DocumentChunk


class WordChunker:
    def __init__(self, chunk_size: int = 400, overlap: int = 60) -> None:
        if chunk_size < 2 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("Invalid chunk_size/chunk_overlap")
        self.chunk_size = chunk_size
        self.overlap = overlap

    @staticmethod
    def _section(text: str) -> str | None:
        for line in text.splitlines():
            candidate = line.strip()
            if 3 <= len(candidate) <= 120 and len(candidate.split()) <= 15:
                return candidate
        return None

    def split(
        self,
        document_id: str,
        pages: Sequence[tuple[int, str]],
        source_filename: str,
    ) -> list[DocumentChunk]:
        chunks: list[DocumentChunk] = []
        step = self.chunk_size - self.overlap
        for page_number, page_text in pages:
            words = re.findall(r"\S+", page_text)
            section = self._section(page_text)
            for offset in range(0, len(words), step):
                text = " ".join(words[offset : offset + self.chunk_size]).strip()
                if not text:
                    continue
                digest = hashlib.sha256(
                    f"{document_id}:{page_number}:{offset}:{text}".encode("utf-8")
                ).hexdigest()[:16]
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document_id}:{page_number}:{digest}",
                        text=text,
                        metadata=ChunkMetadata(
                            document_id=document_id,
                            page_number=page_number,
                            section=section,
                            source_filename=source_filename,
                        ),
                    )
                )
                if offset + self.chunk_size >= len(words):
                    break
        return chunks
