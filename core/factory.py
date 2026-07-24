from __future__ import annotations

from mcp.client import InProcessMCPClient
from mcp.tools import ReadOnlySQLiteTools
from rag.factory import build_retriever

from .application import AnswerService
from .config import AppConfig, load_config
from .llm import create_llm


def build_answer_service(config: AppConfig | None = None) -> AnswerService:
    selected = config or load_config()
    retriever = build_retriever(selected)
    llm = create_llm(selected.llm)
    tools = ReadOnlySQLiteTools(
        selected.sql.connection, selected.sql.max_rows, selected.sql.timeout_seconds
    )
    return AnswerService(retriever, llm, InProcessMCPClient(tools))
