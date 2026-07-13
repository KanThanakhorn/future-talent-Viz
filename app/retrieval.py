from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from collections import Counter

from .config import settings
from .db import connect
from .embeddings import ModelUnavailable, embed_query, rerank

LOG = logging.getLogger(__name__)
LEGACY_VECTOR_SIZE = 256
RRF_K = 60


def _features(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.lower())
    words = re.findall(r"[a-z0-9][a-z0-9+.#-]*|[\u0e00-\u0e7f]+", normalized)
    chars = re.sub(r"\s+", "", normalized)
    return words + [chars[i : i + 3] for i in range(max(0, len(chars) - 2))]


def embed(text: str) -> list[float]:
    """Legacy feature-hash embedding kept for rollback and before/after evaluation."""
    vector = [0.0] * LEGACY_VECTOR_SIZE
    for token, count in Counter(_features(text)).items():
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest[:4], "big") % LEGACY_VECTOR_SIZE
        vector[index] += (1.0 if digest[4] & 1 else -1.0) * (1.0 + math.log(count))
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [round(value / norm, 6) for value in vector]


def cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _base_rows(conn) -> list[dict]:
    return [dict(row) for row in conn.execute(
        """SELECT c.id,c.content,c.page_start,c.page_end,c.embedding,c.source_type,
                  d.id AS document_id,d.title,d.source,d.source_uri,d.document_type
           FROM chunks c JOIN documents d ON d.id=c.document_id WHERE d.status='ready'"""
    )]


def retrieve_legacy(query: str, limit: int | None = None) -> list[dict]:
    limit = limit or settings.retrieval_limit
    query_vector = embed(query)
    with connect() as conn:
        rows = _base_rows(conn)
    for item in rows:
        item["score"] = cosine(query_vector, json.loads(item.pop("embedding")))
    rows.sort(key=lambda item: item["score"], reverse=True)
    return rows[:limit]


def _fts_tokens(query: str) -> list[str]:
    tokens = re.findall(r"[a-zA-Z0-9][a-zA-Z0-9+.#-]{1,}|[\u0e00-\u0e7f]{2,}", query.lower())
    stopwords = {"what", "which", "where", "when", "does", "from", "with", "that", "this", "are", "the", "and", "how", "many", "เป็น", "จาก", "ของ", "อะไร", "อย่างไร"}
    return list(dict.fromkeys(
        token.strip(".+-#") for token in tokens
        if token.strip(".+-#") and token.strip(".+-#") not in stopwords
    ))[:12]


def _bm25_ranking(conn, query: str, candidates: int) -> list[int]:
    tokens = _fts_tokens(query)
    if not tokens:
        return []
    quoted = [f'"{token.replace(chr(34), chr(34) * 2)}"' for token in tokens]
    try:
        sql = """SELECT c.id,bm25(chunk_fts) AS rank FROM chunk_fts
                 JOIN chunks c ON c.id=chunk_fts.rowid JOIN documents d ON d.id=c.document_id
                 WHERE chunk_fts MATCH ? AND d.status='ready' ORDER BY rank LIMIT ?"""
        # Requiring all meaningful terms sharply reduces generic matches. If a
        # cross-language query has no lexical match, fall back to OR and let the
        # multilingual vector branch carry recall.
        rows = conn.execute(sql, (" AND ".join(quoted), candidates)).fetchall()
        if not rows:
            rows = conn.execute(sql, (" OR ".join(quoted), candidates)).fetchall()
        return [row["id"] for row in rows]
    except Exception as exc:
        LOG.warning("FTS5 query failed, continuing with vector ranking: %s", exc)
        return []


def _vector_ranking(conn, rows: list[dict], query: str, candidates: int) -> tuple[list[int], str]:
    active = conn.execute("SELECT value FROM system_settings WHERE key='active_embedding_model'").fetchone()
    if active:
        model = active["value"]
        try:
            query_vector = embed_query(query)
            vectors = {
                row["chunk_id"]: json.loads(row["embedding"])
                for row in conn.execute("SELECT chunk_id,embedding FROM chunk_embeddings_v2 WHERE model=?", (model,))
            }
            if len(vectors) == len(rows):
                ranked = sorted(rows, key=lambda item: cosine(query_vector, vectors[item["id"]]), reverse=True)
                return [item["id"] for item in ranked[:candidates]], model
        except Exception as exc:
            LOG.warning("Multilingual index unavailable, using verified legacy index: %s", exc)
    query_vector = embed(query)
    ranked = sorted(rows, key=lambda item: cosine(query_vector, json.loads(item["embedding"])), reverse=True)
    return [item["id"] for item in ranked[:candidates]], "local-hash-v1"


def retrieve(query: str, limit: int | None = None, use_reranker: bool = True) -> list[dict]:
    limit = limit or settings.retrieval_limit
    candidates = max(settings.retrieval_candidates, limit * 6)
    with connect() as conn:
        rows = _base_rows(conn)
        by_id = {item["id"]: item for item in rows}
        vector_ids, vector_model = _vector_ranking(conn, rows, query, candidates)
        bm25_ids = _bm25_ranking(conn, query, candidates)

    fused: dict[int, float] = {}
    for ranking in (vector_ids, bm25_ids):
        for rank, chunk_id in enumerate(ranking, 1):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
    for chunk_id in fused:
        if (by_id[chunk_id]["page_start"] or 9999) <= 110:
            fused[chunk_id] += 0.001
    ranked_ids = sorted(fused, key=fused.get, reverse=True)[: max(limit * 3, 15)]
    reranker_name = "disabled"
    rerank_scores: dict[int, float] = {}
    final_scores = {chunk_id: fused[chunk_id] for chunk_id in ranked_ids}
    if use_reranker and settings.enable_reranker and ranked_ids:
        try:
            scores = rerank(query, [by_id[chunk_id]["content"] for chunk_id in ranked_ids])
            rerank_scores = dict(zip(ranked_ids, scores))
            rrf_order = list(ranked_ids)
            reranker_order = sorted(ranked_ids, key=lambda chunk_id: rerank_scores[chunk_id], reverse=True)
            final_scores = {}
            for order in (rrf_order, reranker_order):
                for rank, chunk_id in enumerate(order, 1):
                    final_scores[chunk_id] = final_scores.get(chunk_id, 0.0) + 1.0 / (RRF_K + rank)
            ranked_ids.sort(key=final_scores.get, reverse=True)
            reranker_name = settings.reranker_model
        except Exception as exc:
            LOG.warning("Cross-encoder unavailable; RRF ordering retained: %s", exc)
            reranker_name = "rrf-fallback"
    output = []
    max_score = max(final_scores.values(), default=1.0)
    min_score = min(final_scores.values(), default=0.0)
    span = max_score - min_score or 1.0
    for chunk_id in ranked_ids[:limit]:
        item = by_id[chunk_id]
        item.pop("embedding", None)
        item["score"] = (final_scores[chunk_id] - min_score) / span
        item["retrieval"] = {"vector_model": vector_model, "bm25": bool(bm25_ids), "reranker": reranker_name}
        output.append(item)
    return output
