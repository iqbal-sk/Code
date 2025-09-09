#!/usr/bin/env bash

set -Eeuo pipefail

# Summary:
# - Ensures .env files exist (copies from env.example if missing)
# - Starts Redis in Docker (if not already running)
# - Creates a Python venv and installs dependencies
# - Launches Platform API (FastAPI) and Judge worker with aligned env
# - Streams logs to ./logs and traps signals for clean shutdown

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

BACKEND_PORT=${BACKEND_PORT:-8000}
QUEUE_KEY=${QUEUE_KEY:-submission_queue}
ENV_STATE=${ENV_STATE:-dev}

PLATFORM_ENV_DIR="$ROOT_DIR/Platform/src/config"
PLATFORM_ENV="$PLATFORM_ENV_DIR/.env"
PLATFORM_ENV_EX="$PLATFORM_ENV_DIR/env.example"

JUDGE_ENV_DIR="$ROOT_DIR/judge_service/config"
JUDGE_ENV="$JUDGE_ENV_DIR/.env"
JUDGE_ENV_EX="$JUDGE_ENV_DIR/env.example"

notice() { printf "\033[1;34m[info]\033[0m %s\n" "$*"; }
warn()   { printf "\033[1;33m[warn]\033[0m %s\n" "$*"; }
err()    { printf "\033[1;31m[fail]\033[0m %s\n" "$*"; }

# 1) Ensure .env files exist
if [[ ! -f "$PLATFORM_ENV" ]]; then
  if [[ -f "$PLATFORM_ENV_EX" ]]; then
    notice "Creating Platform .env from env.example"
    cp "$PLATFORM_ENV_EX" "$PLATFORM_ENV"
  else
    err "Missing Platform env.example at $PLATFORM_ENV_EX"; exit 1
  fi
fi

if [[ ! -f "$JUDGE_ENV" ]]; then
  if [[ -f "$JUDGE_ENV_EX" ]]; then
    notice "Creating Judge .env from env.example"
    cp "$JUDGE_ENV_EX" "$JUDGE_ENV"
  else
    err "Missing Judge env.example at $JUDGE_ENV_EX"; exit 1
  fi
fi

# 2) Start Redis via Docker (if desired name not running)
REDIS_CONTAINER=${REDIS_CONTAINER:-redis_local}
REDIS_IMAGE=${REDIS_IMAGE:-redis:7-alpine}

if ! docker ps --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
  if docker ps -a --format '{{.Names}}' | grep -q "^${REDIS_CONTAINER}$"; then
    notice "Starting existing Redis container: $REDIS_CONTAINER"
    docker start "$REDIS_CONTAINER" >/dev/null
  else
    notice "Running Redis container: $REDIS_CONTAINER"
    docker run -d --name "$REDIS_CONTAINER" -p 6379:6379 "$REDIS_IMAGE" >/dev/null
  fi
else
  notice "Redis container already running: $REDIS_CONTAINER"
fi

# 3) Python venv + deps
VENV_DIR="$ROOT_DIR/.venv"
if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  notice "Creating virtualenv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

notice "Installing/updating Python dependencies"
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install -r "$ROOT_DIR/Platform/requirements-dev.txt" >/dev/null

# 4) Align runtime env (override via exported env vars if needed)
export ENV_STATE

# Ensure both services agree on queue key
export DEV_SUBMISSION_QUEUE_KEY="$QUEUE_KEY"   # Platform
export DEV_QUEUE_KEY="$QUEUE_KEY"              # Judge

# Point Judge to the Platform API’s test-case endpoint (by port)
export DEV_TESTCASE_API_FORMAT="http://localhost:${BACKEND_PORT}/api/v1/problems/{problemId}/test-cases?includeHidden=true"

# Default Redis URL (can be overridden by user env)
export DEV_REDIS_URL=${DEV_REDIS_URL:-redis://localhost:6379}

# 5) Launch services
notice "Starting Platform API on :$BACKEND_PORT"
(
  cd "$ROOT_DIR"
  PYTHONPATH="$ROOT_DIR" "$VENV_DIR/bin/uvicorn" Platform.src.main:app \
    --host 0.0.0.0 --port "$BACKEND_PORT" --reload \
    >"$LOG_DIR/platform.log" 2>&1
) &
PLATFORM_PID=$!

# Simple wait for API port to be ready (best-effort)
for _ in {1..30}; do
  if (command -v nc >/dev/null 2>&1 && nc -z localhost "$BACKEND_PORT") || curl -sSf "http://localhost:${BACKEND_PORT}/docs" >/dev/null 2>&1; then
    break
  fi
  sleep 0.5
done

notice "Starting Judge worker"
(
  cd "$ROOT_DIR"
  PYTHONPATH="$ROOT_DIR" "$VENV_DIR/bin/python" judge_service/main.py \
    >"$LOG_DIR/judge.log" 2>&1
) &
JUDGE_PID=$!

notice "Services started"
echo "- Platform:   http://localhost:${BACKEND_PORT} (logs: $LOG_DIR/platform.log)"
echo "- Judge:      PID $JUDGE_PID (logs: $LOG_DIR/judge.log)"
echo "- Redis:      docker container '$REDIS_CONTAINER' on :6379"

cleanup() {
  notice "Shutting down services..."
  kill "$JUDGE_PID" >/dev/null 2>&1 || true
  kill "$PLATFORM_PID" >/dev/null 2>&1 || true
  wait "$JUDGE_PID" "$PLATFORM_PID" 2>/dev/null || true
  notice "Done. Logs in $LOG_DIR"
}

trap cleanup INT TERM
wait "$JUDGE_PID" "$PLATFORM_PID"

