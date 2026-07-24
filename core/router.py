from __future__ import annotations

import re

from .models import Route

SQL_TERMS = {
    "who", "budget", "sponsor", "organization", "organisation", "company", "project",
    "statistics", "statistic", "how many", "count", "total", "average", "percent",
    "ใคร", "งบ", "งบประมาณ", "ผู้สนับสนุน", "องค์กร", "บริษัท", "โครงการ", "สถิติ",
    "กี่", "จำนวน", "รวม", "เฉลี่ย", "ร้อยละ",
}
RAG_TERMS = {
    "why", "explain", "describe", "how", "meaning", "summary", "compare",
    "ทำไม", "อธิบาย", "อย่างไร", "ความหมาย", "สรุป", "เปรียบเทียบ",
}


class KeywordQuestionRouter:
    """Fast, deterministic router; terms are configurable by replacing this implementation."""

    def route(self, question: str) -> Route:
        normalized = re.sub(r"\s+", " ", question.lower())
        sql = any(term in normalized for term in SQL_TERMS)
        rag = any(term in normalized for term in RAG_TERMS)
        if sql and rag:
            return Route.HYBRID
        return Route.SQL if sql else Route.RAG
