from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from .db import init_db, transaction
from .ingest import chunks_from_pages
from .retrieval import embed


def process(document_id: int | None = None, limit: int | None = None) -> tuple[int, int]:
    """OCR queued PDF pages and rebuild affected document indexes.

    Pages remain queued when OCR produces too little text. Existing text-layer content
    is retained and OCR output is appended, so OCR can never silently destroy text.
    """
    if not shutil.which("tesseract") or not shutil.which("pdftoppm"):
        raise RuntimeError("OCR requires both tesseract and pdftoppm on PATH")
    init_db()
    completed = 0
    failed = 0
    with transaction() as conn:
        where = "WHERE p.needs_review=1 AND d.document_type='pdf'"
        params: list[int] = []
        if document_id is not None:
            where += " AND d.id=?"
            params.append(document_id)
        query = f"""SELECT p.id,p.document_id,p.page_number,p.content,d.raw_path,d.source_uri
                    FROM document_pages p JOIN documents d ON d.id=p.document_id {where}
                    ORDER BY d.id,p.page_number"""
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        pages = conn.execute(query, params).fetchall()
        changed_documents: set[int] = set()
        for page in pages:
            try:
                with tempfile.TemporaryDirectory() as temp:
                    prefix = Path(temp) / "page"
                    subprocess.run(
                        ["pdftoppm", "-f", str(page["page_number"]), "-l", str(page["page_number"]), "-r", "220", "-png", "-singlefile", page["raw_path"], str(prefix)],
                        check=True, capture_output=True,
                    )
                    result = subprocess.run(
                        ["tesseract", str(prefix) + ".png", "stdout", "-l", "eng+tha"],
                        check=True, capture_output=True, text=True,
                    )
                ocr_text = result.stdout.strip()
                if len(ocr_text) < 80:
                    raise ValueError("OCR returned too little usable text")
                original = page["content"].strip()
                merged = original + ("\n\n[OCR supplement]\n" if original else "") + ocr_text
                conn.execute(
                    "UPDATE document_pages SET content=?,extraction_method='hybrid-text-ocr',confidence=0.80,needs_review=0 WHERE id=?",
                    (merged, page["id"]),
                )
                conn.execute(
                    "INSERT INTO extraction_logs(source_uri,document_id,page_number,level,stage,message) VALUES(?,?,?,?,?,?)",
                    (page["source_uri"], page["document_id"], page["page_number"], "info", "ocr", "OCR completed; text retained with supplement"),
                )
                changed_documents.add(int(page["document_id"]))
                completed += 1
            except Exception as exc:
                conn.execute(
                    "INSERT INTO extraction_logs(source_uri,document_id,page_number,level,stage,message) VALUES(?,?,?,?,?,?)",
                    (page["source_uri"], page["document_id"], page["page_number"], "error", "ocr", str(exc)[:2000]),
                )
                failed += 1
        for doc_id in changed_documents:
            rows = conn.execute(
                "SELECT page_number,content,extraction_method FROM document_pages WHERE document_id=? ORDER BY page_number",
                (doc_id,),
            ).fetchall()
            conn.execute("DELETE FROM chunks WHERE document_id=?", (doc_id,))
            for index, (start, end, content) in enumerate(chunks_from_pages([row["content"] for row in rows])):
                source_type = "chart_ocr" if any(
                    row["extraction_method"] == "hybrid-text-ocr" and start <= row["page_number"] <= end
                    for row in rows
                ) else "narrative"
                conn.execute(
                    """INSERT INTO chunks(document_id,page_start,page_end,chunk_index,content,content_hash,embedding,source_type)
                       VALUES(?,?,?,?,?,?,?,?)""",
                    (doc_id, start, end, index, content, hashlib.sha256(content.encode()).hexdigest(), json.dumps(embed(content), separators=(",", ":")), source_type),
                )
    return completed, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="OCR pages flagged by the extraction pipeline")
    parser.add_argument("--document-id", type=int)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    completed, failed = process(args.document_id, args.limit)
    print(f"OCR complete: {completed} succeeded, {failed} failed")


if __name__ == "__main__":
    main()
