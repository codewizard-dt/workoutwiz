#!/bin/sh
set -e

pip install -e ".[dev]" --quiet

MANIFEST=${MANIFEST_FILE:-pyproject.toml}
HASH=$(md5sum "$MANIFEST" | cut -d' ' -f1)
APP_PID=""

start_app() {
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
  APP_PID=$!
}

stop_app() {
  if [ -n "$APP_PID" ]; then
    kill "$APP_PID" 2>/dev/null
    wait "$APP_PID" 2>/dev/null || true
    APP_PID=""
  fi
}

start_app

while sleep 3; do
  NEW=$(md5sum "$MANIFEST" | cut -d' ' -f1)
  if [ "$NEW" != "$HASH" ]; then
    echo "[entrypoint] $MANIFEST changed — reinstalling..."
    pip install -e ".[dev]" --quiet
    HASH=$NEW
    stop_app
    start_app
  fi
done
