# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.14.6

FROM python:${PYTHON_VERSION}-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv

RUN python -m venv "$VIRTUAL_ENV"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt


FROM python:${PYTHON_VERSION}-slim-bookworm AS runtime

ARG APP_UID=10001
ARG APP_GID=10001

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    FRT_DATABASE_PATH=/app/data/future_ready_talent.db \
    FRT_DATASET_PATH=/app/future-ready-talent-dataset \
    FRT_MODEL_CACHE_PATH=/app/data/model-cache \
    HF_HOME=/app/data/model-cache/huggingface \
    XDG_CACHE_HOME=/app/data/model-cache

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        libgomp1 \
        poppler-utils \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-tha \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid "$APP_GID" app \
    && useradd --uid "$APP_UID" --gid "$APP_GID" --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /app/data /app/future-ready-talent-dataset \
    && chown -R app:app /app

COPY --from=builder /opt/venv /opt/venv

WORKDIR /app
COPY --chown=app:app app ./app
COPY --chown=app:app frontend ./frontend
COPY --chown=app:app core ./core
COPY --chown=app:app rag ./rag
COPY --chown=app:app mcp ./mcp
COPY --chown=app:app database ./database
COPY --chown=app:app benchmark ./benchmark
COPY --chown=app:app web ./web
COPY --chown=app:app config ./config
COPY --chown=app:app cli.py ./cli.py

RUN python -m compileall -q app core rag mcp database benchmark web cli.py

USER app

EXPOSE 8000
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
