#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEPLOY_BRANCH="${DEPLOY_BRANCH:-main}" bash "$SCRIPT_DIR/rollback-staging.sh" "$@"
