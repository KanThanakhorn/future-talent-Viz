from __future__ import annotations

import logging
import time
from typing import Any

from rag.prompts import answer_prompt

from .interfaces import LLMProvider, Retriever, SQLToolClient
from .models import AnswerResult, Route, ToolEvidence
from .router import KeywordQuestionRouter

LOG = logging.getLogger(__name__)


class AnswerService:
    def __init__(
        self,
        retriever: Retriever,
        llm: LLMProvider,
        sql_client: SQLToolClient,
        router: KeywordQuestionRouter | None = None,
    ) -> None:
        self.retriever = retriever
        self.llm = llm
        self.sql_client = sql_client
        self.router = router or KeywordQuestionRouter()

    @staticmethod
    def _tool_for(question: str) -> str:
        value = question.lower()
        if any(term in value for term in ("budget", "งบ", "fund", "cost", "สถิติ", "statistics")):
            return "search_budget"
        if any(term in value for term in ("company", "organization", "organisation", "บริษัท", "องค์กร", "sponsor")):
            return "search_company"
        if any(term in value for term in ("who", "person", "people", "ใคร", "บุคคล")):
            return "search_people"
        return "search_project"

    def answer(
        self,
        question: str,
        *,
        top_k: int | None = None,
        model: str | None = None,
        reasoning_effort: str | None = None,
    ) -> AnswerResult:
        if not question.strip():
            raise ValueError("Question must not be empty")
        total_started = time.perf_counter()
        route = self.router.route(question)

        retrieval_started = time.perf_counter()
        chunks = self.retriever.retrieve(question, top_k)
        retrieval_time = time.perf_counter() - retrieval_started
        if not chunks:
            raise RuntimeError("No retrieved evidence. Index PDFs before asking questions.")

        sql_items: list[ToolEvidence] = []
        sql_time = 0.0
        if route in {Route.SQL, Route.HYBRID}:
            sql_started = time.perf_counter()
            try:
                sql_items.append(self.sql_client.call_tool(self._tool_for(question), {"query": question}))
            except Exception as exc:
                LOG.warning("sql_tool_failed: %s", exc, extra={"event": "sql_tool_failed"})
            sql_time = time.perf_counter() - sql_started

        prompt = answer_prompt(question, chunks, sql_items)
        llm_started = time.perf_counter()
        generation = self.llm.generate(prompt, model=model, reasoning_effort=reasoning_effort)
        llm_time = time.perf_counter() - llm_started
        total_time = time.perf_counter() - total_started
        timings = {
            "retrieval": retrieval_time,
            "sql": sql_time,
            "llm": llm_time,
            "total": total_time,
        }
        LOG.info("answer_complete", extra={
            "event": "answer_complete", "duration_ms": round(total_time * 1000, 2),
            "result_count": len(chunks), "question_length": len(question),
        })
        evidence = [
            f"{item.chunk.metadata.source_filename} page {item.chunk.metadata.page_number} "
            f"(chunk {item.chunk.chunk_id})"
            for item in chunks
        ]
        evidence.extend(f"{item.tool_name}: {len(item.rows)} row(s)" for item in sql_items)
        return AnswerResult(
            answer=generation.text,
            evidence=evidence,
            chunks=chunks,
            sql_evidence=sql_items,
            route=route,
            model=generation.model,
            execution_time=total_time,
            timings=timings,
            usage=generation.usage,
        )


def result_as_dict(result: AnswerResult) -> dict[str, Any]:
    return {
        "answer": result.answer,
        "evidence": result.evidence,
        "source_pdf": sorted({item.chunk.metadata.source_filename for item in result.chunks}),
        "page_number": [item.chunk.metadata.page_number for item in result.chunks],
        "retrieved_chunk_ids": [item.chunk.chunk_id for item in result.chunks],
        "sql_evidence": [
            {"tool": item.tool_name, "rows": item.rows, "query": item.query}
            for item in result.sql_evidence
        ],
        "route": result.route.value,
        "model": result.model,
        "execution_time": result.execution_time,
        "timings": result.timings,
        "token_usage": {
            "input": result.usage.input_tokens,
            "output": result.usage.output_tokens,
            "total": result.usage.total_tokens,
        },
    }
