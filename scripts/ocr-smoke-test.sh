#!/usr/bin/env bash

set -Eeuo pipefail

BASE_URL="${1:-${SMOKE_BASE_URL:-http://localhost:8000}}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_DIR="${WORK_DIR:-/tmp/pdf-flow-ocr-smoke}"
EMAIL="${OCR_SMOKE_EMAIL:-ocr-smoke@example.com}"
PASSWORD="${OCR_SMOKE_PASSWORD:-SecurePass123!}"
FULL_NAME="${OCR_SMOKE_FULL_NAME:-OCR Smoke User}"
OCR_EXPECTED_TEXT="${OCR_EXPECTED_TEXT:-OCR SMOKE 123}"
POLL_ATTEMPTS="${OCR_SMOKE_POLL_ATTEMPTS:-45}"
POLL_SLEEP_SECONDS="${OCR_SMOKE_POLL_SLEEP_SECONDS:-2}"
READY_ATTEMPTS="${OCR_SMOKE_READY_ATTEMPTS:-20}"
READY_SLEEP_SECONDS="${OCR_SMOKE_READY_SLEEP_SECONDS:-3}"
HEALTH_URL="${BASE_URL%/}/health"
DOCS_URL="${BASE_URL%/}/api/docs"

HTTP_BODY=""
HTTP_STATUS=""
COMPOSE_CMD=()

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required command: $1"
    exit 1
  fi
}

wait_for_url() {
  local url="$1"
  local label="$2"
  local attempt=1

  while (( attempt <= READY_ATTEMPTS )); do
    if curl --fail --silent --show-error \
      --retry 2 \
      --retry-connrefused \
      --retry-delay 1 \
      "$url" >/dev/null; then
      log "$label is reachable"
      return 0
    fi

    log "Waiting for $label ($attempt/$READY_ATTEMPTS)"
    sleep "$READY_SLEEP_SECONDS"
    ((attempt++))
  done

  log "$label did not become reachable in time"
  return 1
}

detect_compose() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
  elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
  else
    log "Neither 'docker compose' nor 'docker-compose' is available"
    exit 1
  fi
}

compose_run() {
  "${COMPOSE_CMD[@]}" "$@"
}

get_backend_container_id() {
  local container_id
  container_id="$(compose_run ps -q backend | tr -d '\r')"
  if [[ -z "$container_id" ]]; then
    log "Could not determine backend container id"
    exit 1
  fi
  printf '%s' "$container_id"
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
    --retry 2
    --retry-connrefused
    --retry-delay 1
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
    --retry 2 \
    --retry-connrefused \
    --retry-delay 1 \
    -o "$body_file" \
    -w "%{http_code}" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    "$@" \
    "$url")"
  HTTP_BODY="$(cat "$body_file")"
  rm -f "$body_file"
}

post_file_multipart() {
  local url="$1"
  local file_path="$2"
  local auth_token="${3:-}"
  local body_file
  local -a curl_args

  body_file="$(mktemp)"
  curl_args=(
    --silent
    --show-error
    --retry 2
    --retry-connrefused
    --retry-delay 1
    -o "$body_file"
    -w "%{http_code}"
    -F "file=@${file_path}"
  )
  if [[ -n "$auth_token" ]]; then
    curl_args+=(-H "Authorization: Bearer $auth_token")
  fi

  HTTP_STATUS="$(curl "${curl_args[@]}" "$url")"
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

register_or_reuse_user() {
  local register_json

  log "Registering OCR smoke-test user: $EMAIL"
  post_json \
    "${BASE_URL%/}/api/v1/auth/register" \
    "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"full_name\":\"$FULL_NAME\"}"
  register_json="$HTTP_BODY"

  if [[ "$HTTP_STATUS" == "400" ]] && printf '%s' "$register_json" | grep -q '"detail":"Email already registered"'; then
    log "OCR smoke-test user already exists, reusing it"
  elif [[ "$HTTP_STATUS" == "201" ]]; then
    log "Register response received"
  else
    log "Register failed (HTTP $HTTP_STATUS): $register_json"
    exit 1
  fi
}

login_user() {
  local login_json

  log "Logging in" >&2
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

  extract_json_value "$login_json" "access_token"
}

promote_user_to_pro() {
  log "Promoting OCR smoke-test user to pro"
  local output

  output="$(
    compose_run exec -T \
      -e SMOKE_EMAIL="$EMAIL" \
      -e SMOKE_ROLE="pro" \
      backend python - <<'PY'
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
with engine.begin() as conn:
    result = conn.execute(
        text("UPDATE users SET role = :role WHERE email = :email"),
        {"role": os.environ["SMOKE_ROLE"], "email": os.environ["SMOKE_EMAIL"]},
    )
    print(result.rowcount)
PY
  )"

  if ! printf '%s' "$output" | tail -n 1 | grep -qx '1'; then
    log "Failed to promote OCR smoke-test user to pro: $output"
    exit 1
  fi
}

generate_ocr_sample_image() {
  local target="$1"
  local container_target="/tmp/ocr-smoke-sample.png"
  local container_id
  mkdir -p "$(dirname "$target")"

  log "Generating OCR sample image"
  container_id="$(get_backend_container_id)"
  compose_run exec -T \
    -e OCR_TEXT="$OCR_EXPECTED_TEXT" \
    -e OCR_OUTPUT_PATH="$container_target" \
    backend python - <<'PY'
import os
from PIL import Image, ImageDraw, ImageFont

text = os.environ["OCR_TEXT"]
output_path = os.environ["OCR_OUTPUT_PATH"]
img = Image.new("RGB", (1400, 420), "white")
draw = ImageDraw.Draw(img)

font = None
for candidate in (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
):
    try:
        font = ImageFont.truetype(candidate, 96)
        break
    except OSError:
        continue

if font is None:
    font = ImageFont.load_default()

draw.text((80, 140), text, fill="black", font=font)
img.save(output_path, format="PNG")
PY

  docker cp "${container_id}:${container_target}" "$target" >/dev/null
  compose_run exec -T backend rm -f "$container_target" >/dev/null 2>&1 || true

  if [[ ! -s "$target" ]]; then
    log "Failed to generate OCR sample image"
    exit 1
  fi
}

main() {
  local token
  local upload_json
  local file_id
  local ocr_json
  local job_id
  local download_target
  local sample_image
  local normalized_text

  require_cmd curl
  require_cmd docker
  detect_compose
  wait_for_url "$HEALTH_URL" "health endpoint"
  wait_for_url "$DOCS_URL" "API docs"

  mkdir -p "$WORK_DIR"
  sample_image="$WORK_DIR/ocr-sample.png"
  download_target="$WORK_DIR/ocr-result.txt"

  register_or_reuse_user
  token="$(login_user)"
  promote_user_to_pro
  generate_ocr_sample_image "$sample_image"

  log "Uploading OCR sample image"
  post_file_multipart \
    "${BASE_URL%/}/api/v1/files/upload" \
    "$sample_image" \
    "$token"
  upload_json="$HTTP_BODY"
  if [[ "$HTTP_STATUS" != "201" ]]; then
    log "OCR upload failed (HTTP $HTTP_STATUS): $upload_json"
    exit 1
  fi
  file_id="$(extract_json_value "$upload_json" "file_id")"

  log "Submitting OCR job"
  post_json \
    "${BASE_URL%/}/api/v1/files/ocr" \
    "{\"file_id\":\"$file_id\",\"language\":\"eng\"}" \
    "$token"
  if [[ "$HTTP_STATUS" != "200" ]]; then
    log "OCR submission failed (HTTP $HTTP_STATUS): $HTTP_BODY"
    exit 1
  fi

  ocr_json="$HTTP_BODY"
  job_id="$(extract_json_value "$ocr_json" "job_id")"
  log "OCR job created: $job_id"

  poll_job_completed "$job_id" "$token" >/dev/null

  log "Downloading OCR result"
  curl --fail --silent --show-error \
    -H "Authorization: Bearer $token" \
    -o "$download_target" \
    "${BASE_URL%/}/api/v1/files/download/$job_id"

  if [[ ! -s "$download_target" ]]; then
    log "OCR result file is empty: $download_target"
    exit 1
  fi

  normalized_text="$(tr -d '\r\n[:space:]' < "$download_target" | tr '[:lower:]' '[:upper:]')"
  if [[ "$normalized_text" != *"OCRSMOKE123"* ]]; then
    log "OCR result did not contain expected text"
    log "Expected: OCRSMOKE123"
    log "Actual: $normalized_text"
    exit 1
  fi

  log "OCR smoke test passed"
  log "OCR result saved to $download_target"
}

main "$@"
