from __future__ import annotations

import hashlib
import logging
import subprocess
from collections.abc import Iterable, Iterator
from pathlib import Path

from core.models import DocumentChunk

from .chunker import WordChunker

LOG = logging.getLogger(__name__)


class PdfTextLoader:
    """Extracts page-aware PDF text with Poppler and emits metadata-rich chunks."""

    def __init__(self, chunker: WordChunker) -> None:
        self.chunker = chunker

    @staticmethod
    def discover(paths: Iterable[str]) -> list[Path]:
        found: set[Path] = set()
        for raw in paths:
            path = Path(raw).expanduser()
            if path.is_file() and path.suffix.lower() == ".pdf":
                found.add(path.resolve())
            elif path.is_dir():
                found.update(item.resolve() for item in path.rglob("*.pdf"))
        return sorted(found)

    @staticmethod
    def extract_pages(path: Path) -> list[tuple[int, str]]:
        try:
            result = subprocess.run(
                ["pdftotext", "-layout", str(path), "-"],
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("pdftotext is required (install poppler-utils)") from exc
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"Could not extract {path.name}: {exc.stderr.strip()}") from exc
        return [(index, text.strip()) for index, text in enumerate(result.stdout.split("\f"), 1) if text.strip()]

    def load(self, paths: Iterable[str]) -> Iterator[DocumentChunk]:
        for path in self.discover(paths):
            document_id = hashlib.sha256(str(path).encode("utf-8")).hexdigest()[:12]
            pages = self.extract_pages(path)
            LOG.info("pdf_extracted", extra={"event": "pdf_extracted", "result_count": len(pages)})
            yield from self.chunker.split(document_id, pages, path.name)
