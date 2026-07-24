from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from core.config import ROOT, load_config
from core.factory import build_answer_service
from core.logging import configure_logging

from .metrics import evaluate


@dataclass(frozen=True)
class BenchmarkRow:
    model_label: str
    model: str
    question_id: str
    latency_seconds: float
    accuracy: float
    retrieved_chunks: int
    citation_quality: float
    hallucination_rate: float
    input_tokens: int
    output_tokens: int
    error: str = ""


def run(
    questions_path: Path,
    models_path: Path,
    output_path: Path,
) -> list[BenchmarkRow]:
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    models = json.loads(models_path.read_text(encoding="utf-8"))
    service = build_answer_service()
    rows: list[BenchmarkRow] = []
    for model_info in models:
        for question in questions:
            try:
                result = service.answer(
                    question["question"],
                    model=model_info["model"],
                    reasoning_effort=model_info.get("reasoning_effort"),
                )
                scores = evaluate(
                    result, question.get("expected_keywords", []), question.get("expected_sources", [])
                )
                rows.append(BenchmarkRow(
                    model_label=model_info["label"],
                    model=model_info["model"],
                    question_id=question["id"],
                    latency_seconds=result.execution_time,
                    accuracy=scores.keyword_accuracy,
                    retrieved_chunks=len(result.chunks),
                    citation_quality=scores.citation_quality,
                    hallucination_rate=scores.hallucination_rate,
                    input_tokens=result.usage.input_tokens,
                    output_tokens=result.usage.output_tokens,
                ))
            except Exception as exc:
                rows.append(BenchmarkRow(
                    model_label=model_info["label"], model=model_info["model"],
                    question_id=question["id"], latency_seconds=0, accuracy=0,
                    retrieved_chunks=0, citation_quality=0, hallucination_rate=1,
                    input_tokens=0, output_tokens=0, error=str(exc),
                ))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_markdown(rows), encoding="utf-8")
    output_path.with_suffix(".json").write_text(
        json.dumps([asdict(row) for row in rows], ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return rows


def _markdown(rows: list[BenchmarkRow]) -> str:
    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# RAG + MCP Benchmark Results", "",
        f"Generated: {generated}", "",
        "| Model | Questions | Avg latency (s) | Accuracy | Chunks | Citation quality | Hallucination rate | Tokens |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for label in dict.fromkeys(row.model_label for row in rows):
        selected = [row for row in rows if row.model_label == label]
        successful = [row for row in selected if not row.error]
        sample = successful or selected
        mean = lambda field: statistics.fmean(getattr(row, field) for row in sample) if sample else 0
        lines.append(
            f"| {label} | {len(successful)}/{len(selected)} | {mean('latency_seconds'):.3f} | "
            f"{mean('accuracy'):.2%} | {mean('retrieved_chunks'):.1f} | "
            f"{mean('citation_quality'):.2%} | {mean('hallucination_rate'):.2%} | "
            f"{sum(row.input_tokens + row.output_tokens for row in successful)} |"
        )
    lines.extend(["", "## Per-question results", "",
                  "| Model | Question | Latency | Accuracy | Chunks | Citations | Hallucination | Error |",
                  "|---|---|---:|---:|---:|---:|---:|---|"])
    for row in rows:
        lines.append(
            f"| {row.model_label} | {row.question_id} | {row.latency_seconds:.3f} | "
            f"{row.accuracy:.2%} | {row.retrieved_chunks} | {row.citation_quality:.2%} | "
            f"{row.hallucination_rate:.2%} | {row.error.replace('|', '/')[:120]} |"
        )
    lines.extend([
        "", "## Metric notes", "",
        "- Accuracy is expected-keyword recall; replace or extend it with a human/judge model for competition scoring.",
        "- Citation quality combines expected-source retrieval and inline citation presence.",
        "- Hallucination rate is the fraction of numeric claims absent from retrieved PDF/SQL evidence.",
        "- Model IDs are configurable in `benchmark/models.json` because account-visible API IDs may differ.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--questions", type=Path, default=ROOT / "benchmark/questions.json")
    parser.add_argument("--models", type=Path, default=ROOT / "benchmark/models.json")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmark/results.md")
    args = parser.parse_args()
    config = load_config()
    configure_logging(config.log_level, config.json_logs)
    rows = run(args.questions, args.models, args.output)
    print(f"Wrote {len(rows)} benchmark rows to {args.output}")


if __name__ == "__main__":
    main()
