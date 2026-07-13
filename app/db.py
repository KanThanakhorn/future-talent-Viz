from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import ROOT, settings


def connect(path: Path | None = None) -> sqlite3.Connection:
    db_path = path or settings.database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | None = None) -> None:
    with connect(path) as conn:
        # Old databases may still contain duplicate title/source pairs. The
        # repair command removes them before this new index can be installed.
        schema = (ROOT / "app" / "schema.sql").read_text(encoding="utf-8")
        try:
            conn.executescript(schema)
        except sqlite3.IntegrityError as exc:
            if "documents.title, documents.source" not in str(exc):
                raise
            conn.executescript(schema.replace(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_documents_title_source ON documents(title, source);", ""
            ))
        columns = {row[1] for row in conn.execute("PRAGMA table_info(chunks)")}
        if "source_type" not in columns:
            conn.execute(
                "ALTER TABLE chunks ADD COLUMN source_type TEXT NOT NULL DEFAULT 'narrative' "
                "CHECK (source_type IN ('narrative', 'chart_ocr'))"
            )
        additions = {
            "industries": (("source_document_id", "INTEGER REFERENCES documents(id)"), ("source_page", "INTEGER")),
            "job_demand": (("demand_value", "REAL"), ("demand_unit", "TEXT")),
            "skill_requirements": (
                ("source_document_id", "INTEGER REFERENCES documents(id)"),
                ("source_page", "INTEGER"),
                ("evidence_scope", "TEXT NOT NULL DEFAULT 'industry'"),
            ),
        }
        for table, specs in additions.items():
            existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            for name, definition in specs:
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")
        from .analytics import seed_analytics

        seed_analytics(conn)


@contextmanager
def transaction(path: Path | None = None) -> Iterator[sqlite3.Connection]:
    conn = connect(path)
    try:
        conn.execute("BEGIN")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
