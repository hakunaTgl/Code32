#!/usr/bin/env bash
set -euo pipefail

# Run the Codex-32 API detached (survives terminal Ctrl+C / tool sessions).
# Writes:
# - logs/uvicorn.out (stdout/stderr)
# - logs/uvicorn.pid (PID)

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PY="$ROOT_DIR/venv/bin/python"

mkdir -p "$ROOT_DIR/logs"

if [[ -x "$VENV_PY" ]]; then
  PY="$VENV_PY"
else
  PY="python"
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"

OUT="$ROOT_DIR/logs/uvicorn.out"
PIDFILE="$ROOT_DIR/logs/uvicorn.pid"

cd "$ROOT_DIR"
nohup "$PY" -m uvicorn main:app \
  --app-dir "$ROOT_DIR" \
  --host "$HOST" \
  --port "$PORT" \
  --log-level "$LOG_LEVEL" \
  > "$OUT" 2>&1 &

echo $! > "$PIDFILE"

echo "started pid=$(cat "$PIDFILE")"
echo "logs: $OUT"
