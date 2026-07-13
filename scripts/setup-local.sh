#!/usr/bin/env sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
DEPS="$ROOT/.python-deps"

echo "Installing Python dependencies into $DEPS"
python3 -m pip install --upgrade --target "$DEPS" -r "$ROOT/requirements.txt"
echo "Local dependencies are ready. Start with: ./scripts/run-local.sh"
