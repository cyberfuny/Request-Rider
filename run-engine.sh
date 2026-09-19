#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export CA_DIR="${CA_DIR:-$ROOT_DIR/data/ca}"
export ENGINE_URL="${ENGINE_URL:-http://127.0.0.1:8081}"
WEB_DIR="$ROOT_DIR/web"
VENV_DIR="$WEB_DIR/.venv"
ENGINE_LOG="$ROOT_DIR/.request-rider-engine.log"
ENGINE_PID=""

ensure_venv() {
  local venv_python="$VENV_DIR/bin/python"

  if [ ! -x "$venv_python" ] || ! "$venv_python" -c "import pip" >/dev/null 2>&1; then
    echo "[run-engine] creating Python virtualenv at $VENV_DIR"
    if command -v virtualenv >/dev/null 2>&1; then
      virtualenv --clear "$VENV_DIR" >/dev/null
    else
      python3 -m venv "$VENV_DIR"
    fi
  fi

  if ! "$venv_python" -c "import django" >/dev/null 2>&1; then
    echo "[run-engine] installing Django dependencies in $VENV_DIR"
    "$venv_python" -m pip install --quiet --disable-pip-version-check --break-system-packages -r "$WEB_DIR/requirements.txt"
  fi
}

start_engine() {
  if curl -fsS "$ENGINE_URL/health" >/dev/null 2>&1; then
    echo "[run-engine] engine already running at $ENGINE_URL"
    return 0
  fi

  echo "[run-engine] starting Go engine"
  (
    cd "$ROOT_DIR/engine"
    exec go run . >>"$ENGINE_LOG" 2>&1
  ) &
  ENGINE_PID=$!

  local attempts=0
  while [ "$attempts" -lt 30 ]; do
    if curl -fsS "$ENGINE_URL/health" >/dev/null 2>&1; then
      echo "[run-engine] engine started on $ENGINE_URL"
      return 0
    fi
    sleep 1
    attempts=$((attempts + 1))
  done

  echo "[run-engine] engine failed to start; see $ENGINE_LOG"
  return 1
}

cleanup() {
  if [ -n "${ENGINE_PID:-}" ] && kill -0 "$ENGINE_PID" 2>/dev/null; then
    kill "$ENGINE_PID" 2>/dev/null || true
    wait "$ENGINE_PID" 2>/dev/null || true
  fi
}

start_engine
trap cleanup EXIT

ensure_venv
cd "$WEB_DIR"

echo "[run-engine] applying Django migrations"
"$VENV_DIR/bin/python" manage.py migrate --noinput

echo "[run-engine] starting Django UI using $VENV_DIR"
ENGINE_URL="$ENGINE_URL" "$VENV_DIR/bin/python" manage.py runserver 127.0.0.1:8000
