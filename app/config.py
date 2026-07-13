from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

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
class Settings:
    database_path: Path = ROOT / os.getenv("FRT_DATABASE_PATH", "data/future_ready_talent.db")
    dataset_path: Path = ROOT / os.getenv("FRT_DATASET_PATH", "future-ready-talent-dataset")
    chunk_words: int = int(os.getenv("FRT_CHUNK_WORDS", "400"))
    chunk_overlap: int = int(os.getenv("FRT_CHUNK_OVERLAP", "60"))
    retrieval_limit: int = int(os.getenv("FRT_RETRIEVAL_LIMIT", "6"))
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5-mini")


settings = Settings()
