#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${DEPLOY_BRANCH:-staging}"
REMOTE="${DEPLOY_REMOTE:-v2}"
COMPOSE_FILE_PATH="${COMPOSE_FILE_PATH:-$ROOT_DIR/docker-compose.yml}"
STATE_DIR="${DEPLOY_STATE_DIR:-$ROOT_DIR/.deploy_state/$BRANCH}"
LAST_SUCCESSFUL_COMMIT_FILE="$STATE_DIR/last_successful_commit"
CURRENT_DEPLOYED_COMMIT_FILE="$STATE_DIR/current_deployed_commit"
CURRENT_DEPLOYED_BRANCH_FILE="$STATE_DIR/current_deployed_branch"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-http://localhost:8000}"
RUN_MIGRATIONS_ON_ROLLBACK="${RUN_MIGRATIONS_ON_ROLLBACK:-0}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
ROLLBACK_LOG="$STATE_DIR/rollback-$TIMESTAMP.log"

mkdir -p "$STATE_DIR"
touch "$ROLLBACK_LOG"
exec > >(tee -a "$ROLLBACK_LOG") 2>&1

declare -a COMPOSE_CMD
declare -a COMPOSE_ENV_ARGS

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required command: $1"
    exit 1
  fi
}

detect_compose() {
  local compose_env_file="${COMPOSE_ENV_FILE:-}"

  if [[ -z "$compose_env_file" && -f "$ROOT_DIR/backend/.env" ]]; then
    compose_env_file="$ROOT_DIR/backend/.env"
  fi

  if [[ -n "$compose_env_file" ]]; then
    if [[ ! -f "$compose_env_file" ]]; then
      log "Compose env file not found: $compose_env_file"
      exit 1
    fi
    COMPOSE_ENV_ARGS=(--env-file "$compose_env_file")
    log "Using Docker Compose env file: $compose_env_file"
  fi

  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose "${COMPOSE_ENV_ARGS[@]}" -f "$COMPOSE_FILE_PATH")
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose "${COMPOSE_ENV_ARGS[@]}" -f "$COMPOSE_FILE_PATH")
  else
    log "Neither 'docker compose' nor 'docker-compose' is available"
    exit 1
  fi
}

compose_run() {
  "${COMPOSE_CMD[@]}" "$@"
}

main() {
  local rollback_commit

  require_cmd git
  require_cmd docker
  detect_compose

  if [[ ! -f "$LAST_SUCCESSFUL_COMMIT_FILE" ]]; then
    log "No successful deployment record found"
    exit 1
  fi

  rollback_commit="$(<"$LAST_SUCCESSFUL_COMMIT_FILE")"

  if [[ -z "$rollback_commit" ]]; then
    log "Rollback commit record is empty"
    exit 1
  fi

  log "Rolling back to $rollback_commit"

  git -C "$ROOT_DIR" fetch --prune "$REMOTE"
  git -C "$ROOT_DIR" switch --detach "$rollback_commit"

  compose_run up -d --build

  if [[ "$RUN_MIGRATIONS_ON_ROLLBACK" == "1" ]]; then
    log "Running database migrations during rollback"
    compose_run exec -T backend alembic upgrade head
  fi

  "$ROOT_DIR/scripts/smoke-test.sh" "$SMOKE_BASE_URL"

  echo "$rollback_commit" > "$CURRENT_DEPLOYED_COMMIT_FILE"
  echo "DETACHED@$rollback_commit" > "$CURRENT_DEPLOYED_BRANCH_FILE"

  log "Rollback successful"
  log "Note: this is an application rollback only; database backward compatibility is still your responsibility."
}

main "$@"
