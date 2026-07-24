from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

from core.models import ToolEvidence

from .server import SQLMCPServer
from .tools import ReadOnlySQLiteTools


class InProcessMCPClient:
    """Low-latency MCP client using the same JSON-RPC boundary without a subprocess."""

    def __init__(self, tools: ReadOnlySQLiteTools) -> None:
        self.server = SQLMCPServer(tools)
        self._request_id = 0

    def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolEvidence:
        self._request_id += 1
        response = self.server.handle({
            "jsonrpc": "2.0", "id": self._request_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        })
        if response is None or "error" in response:
            raise RuntimeError((response or {}).get("error", {}).get("message", "MCP call failed"))
        data = response["result"]["structuredContent"]
        return ToolEvidence(data["tool_name"], data["rows"], data.get("query"))


class StdioMCPClient:
    """MCP stdio client useful for integration and external-process isolation."""

    def __init__(self, command: list[str] | None = None) -> None:
        self.command = command or [sys.executable, "-m", "mcp.server"]
        self._request_id = 0

    def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolEvidence:
        self._request_id += 1
        request = json.dumps({
            "jsonrpc": "2.0", "id": self._request_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        }) + "\n"
        completed = subprocess.run(
            self.command, input=request, text=True, capture_output=True, check=True, timeout=10
        )
        response = json.loads(completed.stdout.splitlines()[-1])
        if "error" in response:
            raise RuntimeError(response["error"]["message"])
        data = response["result"]["structuredContent"]
        return ToolEvidence(data["tool_name"], data["rows"], data.get("query"))
