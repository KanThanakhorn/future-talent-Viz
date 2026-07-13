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
        conn.executescript((ROOT / "app" / "schema.sql").read_text(encoding="utf-8"))
        columns = {row[1] for row in conn.execute("PRAGMA table_info(chunks)")}
        if "source_type" not in columns:
            conn.execute(
                "ALTER TABLE chunks ADD COLUMN source_type TEXT NOT NULL DEFAULT 'narrative' "
                "CHECK (source_type IN ('narrative', 'chart_ocr'))"
            )
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
