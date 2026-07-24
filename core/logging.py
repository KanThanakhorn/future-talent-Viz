from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from typing import Iterator


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("event", "duration_ms", "question_length", "result_count"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(level: str = "INFO", json_output: bool = True) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter() if json_output else logging.Formatter("%(levelname)s %(name)s: %(message)s"))
    logging.basicConfig(level=level, handlers=[handler], force=True)


@contextmanager
def logged_timer(logger: logging.Logger, event: str) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        logger.info(event, extra={"event": event, "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
