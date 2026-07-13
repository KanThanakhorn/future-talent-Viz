from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.retrieval import retrieve, retrieve_legacy

ROOT = Path(__file__).resolve().parents[1]


def is_hit(result: dict, expected: dict) -> bool:
    if result["title"] != expected["document"]:
        return False
    start, end = result["page_start"] or 0, result["page_end"] or result["page_start"] or 0
    return any(start <= page <= end for page in expected["pages"])


def evaluate(use_reranker: bool = True) -> dict:
    cases = json.loads((ROOT / "evaluation" / "retrieval_questions.json").read_text(encoding="utf-8"))
    details = []
    before_hits = after_hits = 0
    for case in cases:
        before = retrieve_legacy(case["question"], 3)
        after = retrieve(case["question"], 3, use_reranker=use_reranker)
        before_hit = any(is_hit(result, case) for result in before)
        after_hit = any(is_hit(result, case) for result in after)
        before_hits += before_hit
        after_hits += after_hit
        details.append({
            "id": case["id"], "before_hit@3": before_hit, "after_hit@3": after_hit,
            "before_pages": [[row["title"], row["page_start"]] for row in before],
            "after_pages": [[row["title"], row["page_start"]] for row in after],
        })
    total = len(cases)
    return {
        "cases": total,
        "metric": "document-and-page overlap hit@3",
        "before": {"retriever": "legacy feature hashing", "hits": before_hits, "hit_rate": round(before_hits / total, 4)},
        "after": {"retriever": "BM25 + active vector via RRF + reranker", "hits": after_hits, "hit_rate": round(after_hits / total, 4)},
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reranker", action="store_true")
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation" / "retrieval_report.json")
    args = parser.parse_args()
    report = evaluate(not args.no_reranker)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("cases", "metric", "before", "after")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
