from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv() -> None:
    path = ROOT / ".env"
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


_load_dotenv()


@dataclass(frozen=True)
class RagConfig:
    pdf_paths: tuple[str, ...]
    chunk_size: int
    chunk_overlap: int
    top_k: int
    embedding_provider: str
    embedding_model: str
    vector_backend: str
    vector_store_path: Path


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    temperature: float
    timeout_seconds: float
    api_key: str


@dataclass(frozen=True)
class SQLConfig:
    backend: str
    connection: Path
    max_rows: int
    timeout_seconds: float


@dataclass(frozen=True)
class AppConfig:
    rag: RagConfig
    llm: LLMConfig
    sql: SQLConfig
    log_level: str
    json_logs: bool


def _absolute(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_config(path: str | Path | None = None) -> AppConfig:
    config_path = Path(path or os.getenv("FRT_CONFIG", ROOT / "config/settings.json"))
    raw: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    rag, llm, sql = raw["rag"], raw["llm"], raw["sql"]
    configured_paths = filter(None, os.getenv("FRT_PDF_PATHS", ",".join(rag["pdf_paths"])).split(","))
    pdf_paths = tuple(str(_absolute(item.strip())) for item in configured_paths)
    chunk_size = int(os.getenv("FRT_CHUNK_SIZE", rag["chunk_size"]))
    overlap = int(os.getenv("FRT_CHUNK_OVERLAP", rag["chunk_overlap"]))
    if chunk_size < 2 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("chunk_size must be >= 2 and chunk_overlap must be between 0 and chunk_size - 1")
    return AppConfig(
        rag=RagConfig(
            pdf_paths=pdf_paths,
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            top_k=int(os.getenv("FRT_TOP_K", rag["top_k"])),
            embedding_provider=os.getenv("FRT_EMBEDDING_PROVIDER", rag["embedding_provider"]),
            embedding_model=os.getenv("FRT_EMBEDDING_MODEL", rag["embedding_model"]),
            vector_backend=os.getenv("FRT_VECTOR_BACKEND", rag["vector_backend"]),
            vector_store_path=_absolute(os.getenv("FRT_VECTOR_STORE_PATH", rag["vector_store_path"])),
        ),
        llm=LLMConfig(
            provider=os.getenv("FRT_LLM_PROVIDER", llm["provider"]),
            model=os.getenv("OPENAI_MODEL", llm["model"]),
            temperature=float(os.getenv("FRT_TEMPERATURE", llm["temperature"])),
            timeout_seconds=float(os.getenv("FRT_LLM_TIMEOUT", llm["timeout_seconds"])),
            api_key=os.getenv("OPENAI_API_KEY", ""),
        ),
        sql=SQLConfig(
            backend=os.getenv("FRT_SQL_BACKEND", sql["backend"]),
            connection=_absolute(os.getenv("FRT_DATABASE_PATH", sql["connection"])),
            max_rows=int(os.getenv("FRT_SQL_MAX_ROWS", sql["max_rows"])),
            timeout_seconds=float(os.getenv("FRT_SQL_TIMEOUT", sql["timeout_seconds"])),
        ),
        log_level=raw["logging"]["level"],
        json_logs=bool(raw["logging"]["json"]),
    )
