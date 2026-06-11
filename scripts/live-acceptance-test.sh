#!/usr/bin/env bash

set -Eeuo pipefail

BASE_URL="${1:-${LIVE_BASE_URL:-https://pdf.pawn.eu.org}}"
EMAIL="${LIVE_ADMIN_EMAIL:-}"
PASSWORD="${LIVE_ADMIN_PASSWORD:-}"
RUN_ID="${LIVE_RUN_ID:-$(date +%s)}"

HTTP_BODY=""
HTTP_STATUS=""

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*"
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    log "Missing required command: $1"
    exit 1
  fi
}

request() {
  local method="$1"
  local url="$2"
  shift 2
  local body_file
  body_file="$(mktemp)"

  HTTP_STATUS="$(curl --silent --show-error \
    --retry 2 \
    --retry-connrefused \
    --retry-delay 1 \
    -X "$method" \
    -o "$body_file" \
    -w "%{http_code}" \
    "$@" \
    "$url")"
  HTTP_BODY="$(cat "$body_file")"
  rm -f "$body_file"
}

assert_status() {
  local expected="$1"
  local label="$2"
  if [[ "$HTTP_STATUS" != "$expected" ]]; then
    log "$label failed (HTTP $HTTP_STATUS): $HTTP_BODY"
    exit 1
  fi
  log "$label passed"
}

assert_body_contains() {
  local needle="$1"
  local label="$2"
  if [[ "$HTTP_BODY" != *"$needle"* ]]; then
    log "$label failed; expected response to contain: $needle"
    log "Response: $HTTP_BODY"
    exit 1
  fi
  log "$label passed"
}

extract_json_value() {
  local key="$1"
  local value
  value="$(printf '%s' "$HTTP_BODY" | sed -n "s/.*\"$key\":\"\\([^\"]*\\)\".*/\\1/p" | head -n 1)"
  if [[ -z "$value" ]]; then
    log "Could not extract '$key' from response: $HTTP_BODY"
    exit 1
  fi
  printf '%s' "$value"
}

require_cmd curl

BASE_URL="${BASE_URL%/}"
log "Running live acceptance checks against $BASE_URL"

request GET "$BASE_URL/"
assert_status "200" "frontend homepage"
assert_body_contains "<div id=\"app\"></div>" "frontend app shell"

request GET "$BASE_URL/health"
assert_status "200" "backend health"
assert_body_contains "\"status\":\"healthy\"" "backend health body"

request GET "$BASE_URL/api/v1/admin/public-config"
assert_status "200" "public config"
assert_body_contains "\"feature_flags\"" "public config body"

request GET "$BASE_URL/control-room"
assert_status "200" "control room SPA route"
assert_body_contains "<div id=\"app\"></div>" "control room app shell"

request POST "$BASE_URL/api/v1/feedback" \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"live acceptance ${RUN_ID}\",\"message\":\"Live acceptance feedback probe ${RUN_ID}\",\"category\":\"suggestion\",\"severity\":\"normal\",\"page_url\":\"${BASE_URL}\"}"
assert_status "200" "public feedback submission"
assert_body_contains "\"status\":\"new\"" "public feedback response"

if [[ -n "$EMAIL" && -n "$PASSWORD" ]]; then
  log "Admin credentials provided; checking hidden health report"
  request POST "$BASE_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=$EMAIL" \
    --data-urlencode "password=$PASSWORD"
  assert_status "200" "admin login"
  TOKEN="$(extract_json_value "access_token")"

  request GET "$BASE_URL/api/v1/admin/health-report" \
    -H "Authorization: Bearer $TOKEN"
  assert_status "200" "admin health report"
  assert_body_contains "\"migration_version\"" "admin health report migration"
  assert_body_contains "\"services\"" "admin health report services"
else
  log "Skipping admin health report check; set LIVE_ADMIN_EMAIL and LIVE_ADMIN_PASSWORD to enable it"
fi

log "Live acceptance checks passed"
