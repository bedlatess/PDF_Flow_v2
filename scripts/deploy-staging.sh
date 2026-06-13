#!/usr/bin/env bash

set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BRANCH="${DEPLOY_BRANCH:-staging}"
REMOTE="${DEPLOY_REMOTE:-v2}"
COMPOSE_FILE_PATH="${COMPOSE_FILE_PATH:-$ROOT_DIR/docker-compose.yml}"
STATE_DIR="${DEPLOY_STATE_DIR:-$ROOT_DIR/.deploy_state/$BRANCH}"
BACKUP_DIR="${DEPLOY_BACKUP_DIR:-$ROOT_DIR/.deploy_backups/$BRANCH}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
DEPLOY_LOG="$STATE_DIR/deploy-$TIMESTAMP.log"
LAST_SUCCESSFUL_COMMIT_FILE="$STATE_DIR/last_successful_commit"
CURRENT_DEPLOYED_COMMIT_FILE="$STATE_DIR/current_deployed_commit"
CURRENT_DEPLOYED_BRANCH_FILE="$STATE_DIR/current_deployed_branch"
LAST_SUCCESSFUL_AT_FILE="$STATE_DIR/last_successful_at"
SMOKE_BASE_URL="${SMOKE_BASE_URL:-http://localhost:8000}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"
BACKUP_COMMAND="${DEPLOY_BACKUP_COMMAND:-}"

mkdir -p "$STATE_DIR" "$BACKUP_DIR"
touch "$DEPLOY_LOG"
exec > >(tee -a "$DEPLOY_LOG") 2>&1

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

backup_file_if_present() {
  local relative_path="$1"
  local backup_target_dir="$2"

  if [[ -f "$ROOT_DIR/$relative_path" ]]; then
    mkdir -p "$(dirname "$backup_target_dir/$relative_path")"
    cp "$ROOT_DIR/$relative_path" "$backup_target_dir/$relative_path"
  fi
}

ensure_clean_worktree() {
  if ! git -C "$ROOT_DIR" diff --quiet || ! git -C "$ROOT_DIR" diff --cached --quiet; then
    log "Tracked local changes detected on server. Refusing to deploy."
    log "Please commit/stash/reset server-side tracked changes before running this script."
    exit 1
  fi
}

run_backup() {
  local backup_path="$BACKUP_DIR/$TIMESTAMP"
  local current_commit current_ref

  current_commit="$(git -C "$ROOT_DIR" rev-parse HEAD)"
  current_ref="$(git -C "$ROOT_DIR" symbolic-ref --quiet --short HEAD || echo DETACHED)"

  mkdir -p "$backup_path"

  {
    echo "timestamp=$TIMESTAMP"
    echo "commit=$current_commit"
    echo "ref=$current_ref"
  } > "$backup_path/metadata.txt"

  backup_file_if_present ".env" "$backup_path"
  backup_file_if_present "backend/.env" "$backup_path"
  backup_file_if_present "docker-compose.override.yml" "$backup_path"
  backup_file_if_present "backend/docker-compose.override.yml" "$backup_path"

  if [[ -n "$BACKUP_COMMAND" ]]; then
    log "Running custom backup command"
    BACKUP_PATH="$backup_path" ROOT_DIR="$ROOT_DIR" bash -lc "$BACKUP_COMMAND"
  fi

  log "Backup created at $backup_path"
}

checkout_branch() {
  git -C "$ROOT_DIR" fetch --prune "$REMOTE"

  if ! git -C "$ROOT_DIR" show-ref --verify --quiet "refs/remotes/$REMOTE/$BRANCH"; then
    log "Remote branch '$REMOTE/$BRANCH' does not exist"
    exit 1
  fi

  if git -C "$ROOT_DIR" show-ref --verify --quiet "refs/heads/$BRANCH"; then
    git -C "$ROOT_DIR" checkout "$BRANCH"
  else
    git -C "$ROOT_DIR" checkout -b "$BRANCH" "$REMOTE/$BRANCH"
  fi

  git -C "$ROOT_DIR" pull --ff-only "$REMOTE" "$BRANCH"
}

deploy_services() {
  compose_run up -d --build

  if [[ "$RUN_MIGRATIONS" == "1" ]]; then
    log "Running database migrations"
    compose_run exec -T backend alembic upgrade head
  fi
}

run_smoke_test() {
  log "Running smoke tests against $SMOKE_BASE_URL"
  "$ROOT_DIR/scripts/smoke-test.sh" "$SMOKE_BASE_URL"
}

record_success() {
  local deployed_commit
  deployed_commit="$(git -C "$ROOT_DIR" rev-parse HEAD)"

  echo "$deployed_commit" > "$LAST_SUCCESSFUL_COMMIT_FILE"
  echo "$deployed_commit" > "$CURRENT_DEPLOYED_COMMIT_FILE"
  echo "$BRANCH" > "$CURRENT_DEPLOYED_BRANCH_FILE"
  date '+%F %T' > "$LAST_SUCCESSFUL_AT_FILE"

  log "Deployment successful: $deployed_commit"
}

main() {
  log "Starting staging deployment"
  require_cmd git
  require_cmd docker
  detect_compose
  ensure_clean_worktree
  run_backup
  checkout_branch
  deploy_services
  run_smoke_test
  record_success
  log "Done"
}

main "$@"
