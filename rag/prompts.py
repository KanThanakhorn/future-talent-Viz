from __future__ import annotations

from core.models import RetrievedChunk, ToolEvidence


def answer_prompt(question: str, chunks: list[RetrievedChunk], sql_evidence: list[ToolEvidence]) -> str:
    document_blocks = []
    for index, item in enumerate(chunks, 1):
        meta = item.chunk.metadata
        document_blocks.append(
            f"[PDF-{index}] file={meta.source_filename}; page={meta.page_number}; "
            f"chunk_id={item.chunk.chunk_id}; section={meta.section or '-'}\n{item.chunk.text}"
        )
    sql_blocks = [
        f"[SQL-{index}] tool={item.tool_name}; query={item.query or '-'}\n{item.rows}"
        for index, item in enumerate(sql_evidence, 1)
    ]
    return f"""Answer in the same language as the question.
Use only the evidence below. Cite claims inline with [PDF-N] or [SQL-N].
If evidence is insufficient, say so clearly. Never invent facts or citations.

Question: {question}

PDF evidence:
{chr(10).join(document_blocks) or "(none)"}

SQL evidence:
{chr(10).join(sql_blocks) or "(none)"}
"""
