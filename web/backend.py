from __future__ import annotations

from core.application import result_as_dict
from core.factory import build_answer_service


def answer_question(question: str, top_k: int | None = None) -> dict:
    """Shared backend hook for FastAPI or another optional web interface."""
    return result_as_dict(build_answer_service().answer(question, top_k=top_k))
