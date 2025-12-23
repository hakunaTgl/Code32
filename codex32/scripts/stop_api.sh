#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PIDFILE="$ROOT_DIR/logs/uvicorn.pid"

if [[ ! -f "$PIDFILE" ]]; then
  echo "no pid file: $PIDFILE" >&2
  exit 1
fi

PID="$(cat "$PIDFILE" || true)"
if [[ -z "$PID" ]]; then
  echo "empty pid file: $PIDFILE" >&2
  exit 1
fi

if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "stopped pid=$PID"
else
  echo "pid not running: $PID" >&2
fi

rm -f "$PIDFILE"
