#!/usr/bin/env bash

set -Eeuo pipefail

PUBLIC_URL="${PUBLIC_URL:-${1:-https://pdf.pawn.eu.org}}"
ADMIN_URL="${ADMIN_URL:-${2:-}}"
API_URL="${API_URL:-$PUBLIC_URL}"
EMAIL="${LIVE_ADMIN_EMAIL:-}"
PASSWORD="${LIVE_ADMIN_PASSWORD:-}"
RUN_ID="${LIVE_RUN_ID:-$(date +%s)}"
RUN_WRITE_PROBE="${RUN_WRITE_PROBE:-0}"

HTTP_BODY=""
HTTP_STATUS=""
HTTP_HEADERS=""

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
  local body_file headers_file
  body_file="$(mktemp)"
  headers_file="$(mktemp)"

  HTTP_STATUS="$(curl --silent --show-error \
    --retry 2 \
    --retry-connrefused \
    --retry-delay 1 \
    -X "$method" \
    -D "$headers_file" \
    -o "$body_file" \
    -w "%{http_code}" \
    "$@" \
    "$url")"
  HTTP_BODY="$(cat "$body_file")"
  HTTP_HEADERS="$(cat "$headers_file")"
  rm -f "$body_file" "$headers_file"
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

assert_headers_contain() {
  local needle="$1"
  local label="$2"
  if [[ "$HTTP_HEADERS" != *"$needle"* ]]; then
    log "$label failed; expected headers to contain: $needle"
    log "Headers: $HTTP_HEADERS"
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

PUBLIC_URL="${PUBLIC_URL%/}"
ADMIN_URL="${ADMIN_URL%/}"
API_URL="${API_URL%/}"

require_cmd curl

log "Running production acceptance checks"
log "Public URL: $PUBLIC_URL"
log "API URL: $API_URL"
if [[ -n "$ADMIN_URL" ]]; then
  log "Admin URL: $ADMIN_URL"
else
  log "Admin URL not provided; admin frontend checks will be skipped"
fi

request GET "$PUBLIC_URL/"
assert_status "200" "public homepage"
assert_body_contains "<div id=\"app\"></div>" "public app shell"

request GET "$PUBLIC_URL/en/tools/merge"
assert_status "200" "localized public tool route"
assert_body_contains "<div id=\"app\"></div>" "localized public app shell"

request GET "$API_URL/health"
assert_status "200" "backend health"
assert_body_contains "\"status\":\"healthy\"" "backend health body"

request GET "$API_URL/api/v1/admin/public-config"
assert_status "200" "public config"
assert_body_contains "\"feature_flags\"" "public config body"

if [[ -n "$ADMIN_URL" ]]; then
  request GET "$ADMIN_URL/"
  assert_status "200" "admin frontend"
  assert_body_contains "<div id=\"admin-app\"></div>" "admin app shell"
  assert_headers_contain "X-Robots-Tag:" "admin noindex header"

  request GET "$ADMIN_URL/access"
  assert_status "200" "admin access route"
  assert_body_contains "<div id=\"admin-app\"></div>" "admin access app shell"
fi

FEEDBACK_ID=""

if [[ "$RUN_WRITE_PROBE" == "1" ]]; then
  request POST "$API_URL/api/v1/feedback" \
    -H "Content-Type: application/json" \
    -d "{\"title\":\"production acceptance ${RUN_ID}\",\"message\":\"Production acceptance feedback probe ${RUN_ID}\",\"category\":\"suggestion\",\"severity\":\"normal\",\"page_url\":\"${PUBLIC_URL}\"}"
  assert_status "200" "public feedback submission"
  assert_body_contains "\"status\":\"new\"" "public feedback response"
  FEEDBACK_ID="$(printf '%s' "$HTTP_BODY" | sed -n 's/.*"id":\([0-9][0-9]*\).*/\1/p' | head -n 1)"
else
  log "Skipping write probe; set RUN_WRITE_PROBE=1 to submit and clean up a feedback probe"
fi

if [[ -n "$EMAIL" && -n "$PASSWORD" ]]; then
  log "Admin credentials provided; checking protected admin API"
  request POST "$API_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "username=$EMAIL" \
    --data-urlencode "password=$PASSWORD"
  assert_status "200" "admin login"
  TOKEN="$(extract_json_value "access_token")"

  request GET "$API_URL/api/v1/admin/health-report" \
    -H "Authorization: Bearer $TOKEN"
  assert_status "200" "admin health report"
  assert_body_contains "\"migration_version\"" "admin health report migration"
  assert_body_contains "\"services\"" "admin health report services"

  if [[ "$RUN_WRITE_PROBE" == "1" ]]; then
    request POST "$API_URL/api/v1/admin/feedback/cleanup-live-acceptance" \
      -H "Authorization: Bearer $TOKEN"
    assert_status "200" "production acceptance feedback cleanup"
    assert_body_contains "\"closed_count\"" "production acceptance cleanup response"
  fi
else
  log "Skipping protected admin API checks; set LIVE_ADMIN_EMAIL and LIVE_ADMIN_PASSWORD to enable them"
  if [[ -n "$FEEDBACK_ID" ]]; then
    log "Created feedback probe #$FEEDBACK_ID; close it from the admin frontend if you do not run admin cleanup"
  fi
fi

log "Production acceptance checks passed"
