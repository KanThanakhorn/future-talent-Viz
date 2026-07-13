from __future__ import annotations

import argparse
from pathlib import Path

from .config import ROOT, settings
from .db import connect


def _literal(value: object) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bytes):
        return f"X'{value.hex()}'"
    if isinstance(value, (int, float)):
        return repr(value)
    return "'" + str(value).replace("'", "''") + "'"


def _identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def export_sql(output: Path, database: Path | None = None) -> None:
    with connect(database) as conn, output.open("w", encoding="utf-8") as handle:
        handle.write("PRAGMA foreign_keys=OFF;\nBEGIN TRANSACTION;\n")
        objects = conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE sql IS NOT NULL ORDER BY type,name"
        ).fetchall()
        # FTS5 shadow tables are implementation details. Recreate the virtual
        # table from its declaration and rebuild it from canonical chunks.
        regular_tables = [r for r in objects if r["type"] == "table" and not r["name"].startswith("sqlite_")
                          and not r["name"].startswith("chunk_fts")]
        virtual_tables = [r for r in objects if r["type"] == "table" and r["name"] == "chunk_fts"]
        for row in regular_tables:
            handle.write(row["sql"] + ";\n")
        for row in regular_tables:
            table = row["name"]
            columns = [r[1] for r in conn.execute(f"PRAGMA table_info({_identifier(table)})")]
            names = ",".join(_identifier(name) for name in columns)
            for values in conn.execute(f"SELECT {names} FROM {_identifier(table)}"):
                handle.write(f"INSERT INTO {_identifier(table)} VALUES({','.join(_literal(v) for v in values)});\n")
        for row in virtual_tables:
            handle.write(row["sql"] + ";\n")
            handle.write("INSERT INTO chunk_fts(chunk_fts) VALUES('rebuild');\n")
        for kind in ("index", "trigger", "view"):
            for row in objects:
                if row["type"] == kind and not row["name"].startswith("sqlite_"):
                    handle.write(row["sql"] + ";\n")
        handle.write("COMMIT;\nPRAGMA foreign_keys=ON;\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export a complete restorable SQLite SQL dump")
    parser.add_argument("--database", type=Path, default=settings.database_path)
    parser.add_argument("--output", type=Path, default=ROOT / "future_ready_talent_full_dump.sql")
    args = parser.parse_args()
    export_sql(args.output, args.database)
    print(f"Exported {args.database} to {args.output}")


if __name__ == "__main__":
    main()
