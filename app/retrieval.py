from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter

from .config import settings
from .db import connect

VECTOR_SIZE = 256


def _features(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.lower())
    words = re.findall(r"[a-z0-9][a-z0-9+.#-]*|[\u0e00-\u0e7f]+", normalized)
    chars = re.sub(r"\s+", "", normalized)
    grams = [chars[i : i + 3] for i in range(max(0, len(chars) - 2))]
    return words + grams


def embed(text: str) -> list[float]:
    vector = [0.0] * VECTOR_SIZE
    for token, count in Counter(_features(text)).items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % VECTOR_SIZE
        sign = 1.0 if digest[4] & 1 else -1.0
        vector[index] += sign * (1.0 + math.log(count))
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def retrieve(query: str, limit: int | None = None) -> list[dict]:
    limit = limit or settings.retrieval_limit
    query_vector = embed(query)
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.content, c.page_start, c.page_end, c.embedding,
                   d.id AS document_id, d.title, d.source, d.source_uri
            FROM chunks c JOIN documents d ON d.id = c.document_id
            WHERE d.status = 'ready'
            """
        ).fetchall()
    scored = []
    query_terms = {term for term in re.findall(r"[a-z0-9][a-z0-9+.#-]*", query.lower()) if len(term) > 2}
    for row in rows:
        item = dict(row)
        vector_score = cosine(query_vector, json.loads(item.pop("embedding")))
        haystack = f"{item['title']} {item['content']}".lower()
        overlap = sum(1 for term in query_terms if term in haystack) / (len(query_terms) or 1)
        # Main report chapters contain the synthesized findings; appendices remain
        # searchable but should not outrank an equally relevant main-section hit.
        main_section_boost = 0.04 if (item["page_start"] or 9999) <= 110 else 0.0
        item["score"] = 0.72 * vector_score + 0.24 * overlap + main_section_boost
        scored.append(item)
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:limit]
