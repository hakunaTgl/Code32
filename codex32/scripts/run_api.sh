#!/usr/bin/env bash
set -euo pipefail

# Run the Codex-32 API locally in a way that works even if your shell PATH
# doesn't include the virtualenv's executables.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$ROOT_DIR/venv/bin/python"

if [[ -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
else
  # Fall back to whatever python is on PATH.
  PY="python"
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"

cd "$ROOT_DIR"
exec "$PY" -m uvicorn main:app \
  --app-dir "$ROOT_DIR" \
  --host "$HOST" \
  --port "$PORT" \
  --log-level "$LOG_LEVEL"
