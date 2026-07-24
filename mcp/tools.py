from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.models import ToolEvidence

READ_ACTIONS = {
    sqlite3.SQLITE_SELECT,
    sqlite3.SQLITE_READ,
    sqlite3.SQLITE_FUNCTION,
    sqlite3.SQLITE_RECURSIVE,
}
DENIED_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|VACUUM|ATTACH|DETACH|"
    r"PRAGMA|REINDEX|ANALYZE|BEGIN|COMMIT|ROLLBACK|SAVEPOINT|RELEASE)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]


TOOL_DEFINITIONS = [
    ToolDefinition("search_people", "Search people in available structured records.", {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
    }),
    ToolDefinition("search_budget", "Search budget, cost, funding, and numeric metrics.", {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
    }),
    ToolDefinition("search_company", "Search organizations, companies, and industries.", {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
    }),
    ToolDefinition("search_project", "Search projects, job roles, and editorial records.", {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
    }),
    ToolDefinition("execute_readonly_sql", "Execute one read-only SELECT or WITH query.", {
        "type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]
    }),
]


class ReadOnlySQLiteTools:
    def __init__(self, database_path: Path, max_rows: int = 100, timeout: float = 3.0) -> None:
        self.database_path = database_path
        self.max_rows = max_rows
        self.timeout = timeout

    def _connect(self) -> sqlite3.Connection:
        uri = f"file:{self.database_path.resolve()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=self.timeout)
        conn.row_factory = sqlite3.Row
        conn.execute(f"PRAGMA busy_timeout={int(self.timeout * 1000)}")

        def authorizer(action: int, _arg1: str | None, _arg2: str | None, _db: str | None, _source: str | None) -> int:
            return sqlite3.SQLITE_OK if action in READ_ACTIONS else sqlite3.SQLITE_DENY

        conn.set_authorizer(authorizer)
        return conn

    @staticmethod
    def _validate(query: str) -> str:
        cleaned = query.strip().rstrip(";").strip()
        if not cleaned or ";" in cleaned:
            raise ValueError("Exactly one SQL statement is allowed")
        if DENIED_KEYWORDS.search(cleaned) or not re.match(r"^(SELECT|WITH)\b", cleaned, re.IGNORECASE):
            raise ValueError("Only read-only SELECT/WITH statements are allowed")
        return cleaned

    def execute_readonly_sql(self, query: str) -> ToolEvidence:
        cleaned = self._validate(query)
        wrapped = f"SELECT * FROM ({cleaned}) LIMIT ?"
        with self._connect() as conn:
            rows = [dict(row) for row in conn.execute(wrapped, (self.max_rows,)).fetchall()]
        return ToolEvidence("execute_readonly_sql", rows, cleaned)

    def _table_exists(self, name: str) -> bool:
        try:
            result = self.execute_readonly_sql(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{name}'"
            )
            return bool(result.rows)
        except sqlite3.Error:
            return False

    @staticmethod
    def _like(query: str) -> str:
        return f"%{query.strip()}%"

    def search_people(self, query: str) -> ToolEvidence:
        if not self._table_exists("people"):
            return ToolEvidence("search_people", [], "people table is not present")
        evidence = self.execute_readonly_sql(
            "SELECT * FROM people WHERE name LIKE " + _sql_literal(self._like(query))
        )
        return ToolEvidence("search_people", evidence.rows, evidence.query)

    def search_budget(self, query: str) -> ToolEvidence:
        value = _sql_literal(self._like(query))
        if not self._table_exists("analytics_metrics") and self._table_exists("projects"):
            evidence = self.execute_readonly_sql(
                "SELECT p.name,p.budget,p.currency,p.source_document_id,p.source_page,"
                "c.name AS company FROM projects p LEFT JOIN companies c ON c.id=p.company_id "
                f"WHERE p.name LIKE {value} OR c.name LIKE {value}"
            )
            return ToolEvidence("search_budget", evidence.rows, evidence.query)
        if not self._table_exists("analytics_metrics"):
            return ToolEvidence("search_budget", [], "No budget-compatible table is present")
        evidence = self.execute_readonly_sql(
            "SELECT a.label,a.value,a.unit,a.period,a.scope,a.source_page,"
            "d.title AS source_title FROM analytics_metrics a "
            "JOIN documents d ON d.id=a.source_document_id "
            f"WHERE a.label LIKE {value} OR a.note LIKE {value} OR a.chart_key LIKE {value}"
        )
        return ToolEvidence("search_budget", evidence.rows, evidence.query)

    def search_company(self, query: str) -> ToolEvidence:
        value = _sql_literal(self._like(query))
        if not self._table_exists("industries") and self._table_exists("companies"):
            evidence = self.execute_readonly_sql(
                "SELECT name,description,source_document_id,source_page FROM companies "
                f"WHERE name LIKE {value} OR description LIKE {value}"
            )
            return ToolEvidence("search_company", evidence.rows, evidence.query)
        if not self._table_exists("industries"):
            return ToolEvidence("search_company", [], "No company-compatible table is present")
        evidence = self.execute_readonly_sql(
            "SELECT i.name,i.description,i.source_page,d.title AS source_title "
            "FROM industries i LEFT JOIN documents d ON d.id=i.source_document_id "
            f"WHERE i.name LIKE {value} OR i.description LIKE {value}"
        )
        return ToolEvidence("search_company", evidence.rows, evidence.query)

    def search_project(self, query: str) -> ToolEvidence:
        value = _sql_literal(self._like(query))
        if not self._table_exists("job_demand") and self._table_exists("projects"):
            evidence = self.execute_readonly_sql(
                "SELECT p.name,p.budget,p.currency,p.source_document_id,p.source_page,"
                "c.name AS company FROM projects p LEFT JOIN companies c ON c.id=p.company_id "
                f"WHERE p.name LIKE {value} OR c.name LIKE {value}"
            )
            return ToolEvidence("search_project", evidence.rows, evidence.query)
        if not self._table_exists("job_demand"):
            return ToolEvidence("search_project", [], "No project-compatible table is present")
        evidence = self.execute_readonly_sql(
            "SELECT j.job_role,j.headcount_needed,j.demand_value,j.demand_unit,j.year_start,"
            "j.year_end,j.source_page,d.title AS source_title FROM job_demand j "
            "JOIN documents d ON d.id=j.source_document_id "
            f"WHERE j.job_role LIKE {value} OR j.note LIKE {value}"
        )
        return ToolEvidence("search_project", evidence.rows, evidence.query)

    def call(self, name: str, arguments: dict[str, Any]) -> ToolEvidence:
        handlers = {
            "search_people": self.search_people,
            "search_budget": self.search_budget,
            "search_company": self.search_company,
            "search_project": self.search_project,
            "execute_readonly_sql": self.execute_readonly_sql,
        }
        if name not in handlers:
            raise ValueError(f"Unknown tool: {name}")
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        return handlers[name](query)


def _sql_literal(value: str) -> str:
    """Quote an internally constructed search value; arbitrary SQL uses bound validation."""
    return "'" + value.replace("'", "''") + "'"
