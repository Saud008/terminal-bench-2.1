#!/usr/bin/env bash
# Validate icc.stage.json schema before export.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

validate_staging_file() {
  local staging_path="$1"
  require_file "${staging_path}"
  jq -e '.schema == "icc-softproof-stage/1" and (.patches | type) == "array"' "${staging_path}" >/dev/null
}
