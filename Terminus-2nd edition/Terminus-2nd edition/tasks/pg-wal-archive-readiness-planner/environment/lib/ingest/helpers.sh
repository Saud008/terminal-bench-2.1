#!/usr/bin/env bash
# Ingest-stage helpers (staging path validation).
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

validate_ingest_paths() {
  local archive="$1"
  local staging="$2"
  [[ -d "${archive}" ]] || die "archive not found: ${archive}"
  [[ -n "${staging}" ]] || die "staging path required"
}
