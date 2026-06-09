#!/usr/bin/env bash

set -Eeuo pipefail

BASE_URL="${1:-${SMOKE_BASE_URL:-http://localhost:8000}}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FIXTURE_DIR="${FIXTURE_DIR:-$ROOT_DIR/tests/fixtures}"
WORK_DIR="${WORK_DIR:-/tmp/pdf-flow-business-smoke}"
EMAIL="${BUSINESS_SMOKE_EMAIL:-smoke@example.com}"
PASSWORD="${BUSINESS_SMOKE_PASSWORD:-SecurePass123!}"
FULL_NAME="${BUSINESS_SMOKE_FULL_NAME:-Smoke Test User}"
POLL_ATTEMPTS="${BUSINESS_SMOKE_POLL_ATTEMPTS:-30}"
POLL_SLEEP_SECONDS="${BUSINESS_SMOKE_POLL_SLEEP_SECONDS:-2}"

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

HTTP_BODY=""
HTTP_STATUS=""

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required command: $1"
    exit 1
  fi
}

require_file() {
  if [[ ! -f "$1" ]]; then
    log "Missing required file: $1"
    exit 1
  fi
}

extract_json_value() {
  local json_input="$1"
  local key="$2"
  local value

  value="$(printf '%s' "$json_input" | sed -n "s/.*\"$key\":\"\\([^\"]*\\)\".*/\\1/p" | head -n 1)"
  if [[ -z "$value" ]]; then
    log "Could not extract '$key' from response: $json_input"
    exit 1
  fi
  printf '%s' "$value"
}

post_json() {
  local url="$1"
  local payload="$2"
  local auth_token="${3:-}"
  local body_file
  local -a curl_args
  body_file="$(mktemp)"
  curl_args=(
    --silent
    --show-error
    -o "$body_file"
    -w "%{http_code}"
    -H "Content-Type: application/json"
    -d "$payload"
  )
  if [[ -n "$auth_token" ]]; then
    curl_args+=(-H "Authorization: Bearer $auth_token")
  fi
  HTTP_STATUS="$(curl "${curl_args[@]}" "$url")"
  HTTP_BODY="$(cat "$body_file")"
  rm -f "$body_file"
}

post_form_urlencoded() {
  local url="$1"
  shift
  local body_file
  body_file="$(mktemp)"
  HTTP_STATUS="$(curl --silent --show-error \
    -o "$body_file" \
    -w "%{http_code}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    "$@" \
    "$url")"
  HTTP_BODY="$(cat "$body_file")"
  rm -f "$body_file"
}

poll_job_completed() {
  local job_id="$1"
  local token="$2"
  local status_json
  local status_value

  for ((attempt=1; attempt<=POLL_ATTEMPTS; attempt++)); do
    status_json="$(curl --fail --silent --show-error \
      -H "Authorization: Bearer $token" \
      "${BASE_URL%/}/api/v1/files/jobs/$job_id")"
    status_value="$(extract_json_value "$status_json" "status")"

    if [[ "$status_value" == "completed" ]]; then
      log "Job $job_id completed"
      printf '%s' "$status_json"
      return 0
    fi

    if [[ "$status_value" == "failed" ]]; then
      log "Job $job_id failed: $status_json"
      return 1
    fi

    log "Waiting for job $job_id ($attempt/$POLL_ATTEMPTS), status=$status_value"
    sleep "$POLL_SLEEP_SECONDS"
  done

  log "Job $job_id did not complete in time"
  return 1
}

main() {
  local register_json
  local login_json
  local token
  local upload1_json
  local upload2_json
  local file1_id
  local file2_id
  local merge_json
  local job_id
  local download_target
  local sample1="$FIXTURE_DIR/sample1.pdf"
  local sample2="$FIXTURE_DIR/sample2.pdf"

  require_cmd curl
  require_file "$sample1"
  require_file "$sample2"

  mkdir -p "$WORK_DIR"
  download_target="$WORK_DIR/merged.pdf"

  log "Registering smoke-test user: $EMAIL"
  post_json \
    "${BASE_URL%/}/api/v1/auth/register" \
    "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"$FULL_NAME\"}"
  register_json="$HTTP_BODY"
  if [[ "$HTTP_STATUS" == "400" ]] && printf '%s' "$register_json" | grep -q '"detail":"Email already registered"'; then
    log "Smoke-test user already exists, reusing it"
  elif [[ "$HTTP_STATUS" == "201" ]]; then
    log "Register response received"
  else
    log "Register failed (HTTP $HTTP_STATUS): $register_json"
    exit 1
  fi

  log "Logging in"
  post_form_urlencoded \
    "${BASE_URL%/}/api/v1/auth/login" \
    --data-urlencode "grant_type=password" \
    --data-urlencode "username=$EMAIL" \
    --data-urlencode "password=$PASSWORD"
  login_json="$HTTP_BODY"
  if [[ "$HTTP_STATUS" != "200" ]]; then
    log "Login failed (HTTP $HTTP_STATUS): $login_json"
    exit 1
  fi
  token="$(extract_json_value "$login_json" "access_token")"

  log "Uploading sample1.pdf"
  upload1_json="$(curl --fail --silent --show-error \
    -H "Authorization: Bearer $token" \
    -F "file=@$sample1" \
    "${BASE_URL%/}/api/v1/files/upload")"
  file1_id="$(extract_json_value "$upload1_json" "file_id")"

  log "Uploading sample2.pdf"
  upload2_json="$(curl --fail --silent --show-error \
    -H "Authorization: Bearer $token" \
    -F "file=@$sample2" \
    "${BASE_URL%/}/api/v1/files/upload")"
  file2_id="$(extract_json_value "$upload2_json" "file_id")"

  log "Submitting merge job"
  post_json \
    "${BASE_URL%/}/api/v1/files/merge" \
    "{\"file_ids\":[\"$file1_id\",\"$file2_id\"],\"output_filename\":\"business-smoke-merged.pdf\"}" \
    "$token"
  if [[ "$HTTP_STATUS" != "200" ]]; then
    log "Merge submission failed (HTTP $HTTP_STATUS): $HTTP_BODY"
    exit 1
  fi
  merge_json="$HTTP_BODY"
  job_id="$(extract_json_value "$merge_json" "job_id")"
  log "Merge job created: $job_id"

  poll_job_completed "$job_id" "$token"

  log "Downloading merged result"
  curl --fail --silent --show-error \
    -H "Authorization: Bearer $token" \
    -o "$download_target" \
    "${BASE_URL%/}/api/v1/files/download/$job_id"

  if [[ ! -s "$download_target" ]]; then
    log "Downloaded file is empty: $download_target"
    exit 1
  fi

  log "Business smoke test passed"
  log "Merged file saved to $download_target"
}

main "$@"
