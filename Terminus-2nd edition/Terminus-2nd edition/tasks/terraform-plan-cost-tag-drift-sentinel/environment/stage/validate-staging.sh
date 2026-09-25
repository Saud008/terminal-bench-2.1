#!/usr/bin/env bash
# Validate staging snapshot schema before export phase.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

validate_staging_file() {
  local staging_path="$1"
  [[ -f "${staging_path}" ]] || die "staging missing: ${staging_path}"
  jq -e '.schema == "plan-tag-stage/1" and (.resources | type) == "array"' "${staging_path}" >/dev/null
}
