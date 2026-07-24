from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from typing import Any

from core.config import load_config

from .tools import TOOL_DEFINITIONS, ReadOnlySQLiteTools


class SQLMCPServer:
    def __init__(self, tools: ReadOnlySQLiteTools) -> None:
        self.tools = tools

    def handle(self, request: dict[str, Any]) -> dict[str, Any] | None:
        request_id = request.get("id")
        method = request.get("method")
        if request_id is None:
            return None
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "future-talent-sql", "version": "1.0.0"},
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": [
                    {"name": item.name, "description": item.description, "inputSchema": item.input_schema}
                    for item in TOOL_DEFINITIONS
                ]}
            elif method == "tools/call":
                params = request.get("params", {})
                evidence = self.tools.call(params.get("name", ""), params.get("arguments", {}))
                result = {
                    "content": [{"type": "text", "text": json.dumps(asdict(evidence), ensure_ascii=False)}],
                    "structuredContent": asdict(evidence),
                    "isError": False,
                }
            else:
                return self._error(request_id, -32601, f"Method not found: {method}")
            return {"jsonrpc": "2.0", "id": request_id, "result": result}
        except Exception as exc:
            return self._error(request_id, -32000, str(exc))

    @staticmethod
    def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def serve() -> None:
    config = load_config()
    server = SQLMCPServer(ReadOnlySQLiteTools(
        config.sql.connection, config.sql.max_rows, config.sql.timeout_seconds
    ))
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            response = server.handle(json.loads(line))
        except json.JSONDecodeError as exc:
            response = SQLMCPServer._error(None, -32700, str(exc))
        if response is not None:
            print(json.dumps(response, ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Future Talent read-only SQL MCP server")
    parser.parse_args()
    serve()


if __name__ == "__main__":
    main()
