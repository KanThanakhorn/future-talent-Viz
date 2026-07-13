"""One-time, idempotent repair for the duplicated PDF ingestion incident."""
from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path

from .config import ROOT, settings
from .db import connect, init_db
from .export_sql import export_sql


PAIRS = ((1, 7), (2, 8))


def _same_children(conn, table: str, keep: int, duplicate: int, document_column: str, fields: tuple[str, ...]) -> bool:
    cols = ",".join(fields)
    left = [tuple(r) for r in conn.execute(
        f"SELECT {cols} FROM {table} WHERE {document_column}=? ORDER BY {cols}", (keep,)
    )]
    right = [tuple(r) for r in conn.execute(
        f"SELECT {cols} FROM {table} WHERE {document_column}=? ORDER BY {cols}", (duplicate,)
    )]
    return left == right


def repair(database: Path, backup_dump: Path) -> None:
    binary_backup = backup_dump.with_suffix(".db")
    with connect(database) as probe:
        needs_repair = any(
            probe.execute("SELECT COUNT(*) FROM documents WHERE id IN (?,?)", pair).fetchone()[0] == 2
            for pair in PAIRS
        )
    if needs_repair and (backup_dump.exists() or binary_backup.exists()):
        raise FileExistsError(f"Refusing to overwrite an existing pre-migration backup: {backup_dump}")
    if needs_repair:
        export_sql(backup_dump, database)
        with connect(database) as source, sqlite3.connect(binary_backup) as destination:
            source.backup(destination)

    with connect(database) as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            for keep, duplicate in PAIRS:
                docs = conn.execute(
                    "SELECT id,source_uri,title,source,published_date,topic,document_type,page_count FROM documents WHERE id IN (?,?)",
                    (keep, duplicate),
                ).fetchall()
                if len(docs) < 2:
                    continue
                a, b = docs
                identity_a = (*tuple(a)[2:], os.path.basename(a["source_uri"]))
                identity_b = (*tuple(b)[2:], os.path.basename(b["source_uri"]))
                if identity_a != identity_b:
                    raise RuntimeError(f"Documents {keep}/{duplicate} do not identify the same source")
                checks = (
                    ("document_pages", "document_id", ("page_number","section","content","extraction_method","confidence","needs_review")),
                    ("chunks", "document_id", ("page_start","page_end","chunk_index","content","content_hash","embedding","embedding_model","source_type")),
                    ("analytics_metrics", "source_document_id", ("chart_key","series","label","value","unit","period","scope","sort_order","source_page","note")),
                )
                for table, column, fields in checks:
                    exact = _same_children(conn, table, keep, duplicate, column, fields)
                    if not exact and table == "analytics_metrics":
                        raise RuntimeError(f"Refusing to merge non-identical {table} for documents {keep}/{duplicate}")
                    if not exact:
                        # pdftotext layout can vary between runtime versions.
                        # Require the same logical row keys/count and retain the
                        # explicitly requested lower-id extraction.
                        key = "page_number" if table == "document_pages" else "chunk_index"
                        left = [r[0] for r in conn.execute(f"SELECT {key} FROM {table} WHERE {column}=? ORDER BY {key}", (keep,))]
                        right = [r[0] for r in conn.execute(f"SELECT {key} FROM {table} WHERE {column}=? ORDER BY {key}", (duplicate,))]
                        if left != right:
                            raise RuntimeError(f"Mismatched {table} structure for documents {keep}/{duplicate}")
                    # Exact duplicates cannot be repointed due to unique keys;
                    # deleting their parent chunks also cascades v2 embeddings.
                    conn.execute(f"DELETE FROM {table} WHERE {column}=?", (duplicate,))
                for table, column in (("job_demand","source_document_id"), ("skills","source_document_id"),
                                      ("extraction_logs","document_id"), ("industries","source_document_id"),
                                      ("skill_requirements","source_document_id")):
                    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone():
                        columns = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
                        if column in columns:
                            conn.execute(f"UPDATE {table} SET {column}=? WHERE {column}=?", (keep, duplicate))
                conn.execute("DELETE FROM documents WHERE id=?", (duplicate,))

            stable = {
                1: "dataset://In-depth research on youth NEET in Thailand.pdf",
                2: "dataset://WEF_Future_of_Jobs_Report_2025.pdf",
            }
            for doc_id, uri in stable.items():
                conn.execute("UPDATE documents SET source_uri=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (uri, doc_id))
            conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_title_source ON documents(title,source)")
            analytics = conn.execute(
                """SELECT COUNT(*) FROM analytics_metrics WHERE chart_key IN (
                       'skill_change','macrotrends','neet_provinces','neet_groups',
                       'neet_demographics','readiness_gap'
                   )"""
            ).fetchone()[0]
            if analytics != 37:
                raise RuntimeError(f"Expected 37 analytics rows after repair, found {analytics}")
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise RuntimeError(f"Foreign-key violations after repair: {violations[:5]}")
            conn.execute(
                """UPDATE embedding_indexes SET chunk_count=(
                       SELECT COUNT(*) FROM chunk_embeddings_v2 WHERE model=embedding_indexes.model
                   )"""
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    init_db(database)
    from .ingest import seed_verified_data
    seed_verified_data(database)


def main() -> None:
    parser = argparse.ArgumentParser(description="Repair duplicated documents and dependent rows")
    parser.add_argument("--database", type=Path, default=settings.database_path)
    parser.add_argument("--backup", type=Path, default=ROOT / "future_ready_talent_full_dump_before_database_fix.sql")
    args = parser.parse_args()
    repair(args.database, args.backup)
    print(f"Repair complete; pre-migration dump: {args.backup}")


if __name__ == "__main__":
    main()
