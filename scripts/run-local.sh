#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEPS="$ROOT/.python-deps"

if [ ! -d "$DEPS/fastapi" ] || [ ! -d "$DEPS/uvicorn" ]; then
  echo "Dependencies are missing. Run ./scripts/setup-local.sh first." >&2
  exit 1
fi

cd "$ROOT"
export PYTHONPATH="$DEPS${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 "$@"
