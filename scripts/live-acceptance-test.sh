#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PUBLIC_URL="${LIVE_BASE_URL:-${1:-https://pdf.pawn.eu.org}}" \
API_URL="${LIVE_API_URL:-${LIVE_BASE_URL:-${1:-https://pdf.pawn.eu.org}}}" \
ADMIN_URL="${LIVE_ADMIN_URL:-${2:-}}" \
bash "$SCRIPT_DIR/production-acceptance.sh"
