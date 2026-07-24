from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from core.config import ROOT, load_config


def seed(path: Path | None = None) -> None:
    config = load_config()
    database_path = path or config.sql.connection
    database_path.parent.mkdir(parents=True, exist_ok=True)
    schema = (ROOT / "database/schema.sql").read_text(encoding="utf-8")
    with sqlite3.connect(database_path) as conn:
        conn.executescript(schema)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path)
    args = parser.parse_args()
    seed(args.database)
    print(f"Schema initialized: {args.database or load_config().sql.connection}")


if __name__ == "__main__":
    main()
