from __future__ import annotations

import re
from dataclasses import dataclass

from core.models import AnswerResult


@dataclass(frozen=True)
class Evaluation:
    keyword_accuracy: float
    citation_quality: float
    hallucination_rate: float


def evaluate(result: AnswerResult, expected_keywords: list[str], expected_sources: list[str]) -> Evaluation:
    answer = result.answer.lower()
    keyword_accuracy = (
        sum(keyword.lower() in answer for keyword in expected_keywords) / len(expected_keywords)
        if expected_keywords else 1.0
    )
    retrieved_sources = {item.chunk.metadata.source_filename for item in result.chunks}
    source_recall = (
        sum(source in retrieved_sources for source in expected_sources) / len(expected_sources)
        if expected_sources else 1.0
    )
    cited = bool(re.search(r"\[(?:PDF|SQL)-\d+\]", result.answer))
    citation_quality = (source_recall + float(cited)) / 2

    evidence_text = " ".join(item.chunk.text.lower() for item in result.chunks)
    evidence_text += " " + " ".join(str(item.rows).lower() for item in result.sql_evidence)
    claims = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", result.answer))
    supported = {claim for claim in claims if claim in evidence_text}
    hallucination_rate = (len(claims - supported) / len(claims)) if claims else 0.0
    return Evaluation(keyword_accuracy, citation_quality, hallucination_rate)
