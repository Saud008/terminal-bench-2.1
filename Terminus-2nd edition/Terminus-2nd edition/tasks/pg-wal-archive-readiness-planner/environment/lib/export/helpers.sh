#!/usr/bin/env bash
# Export-stage helpers (planner output path validation).
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

validate_export_paths() {
  local staging="$1"
  local out="$2"
  [[ -f "${staging}" ]] || die "staging missing: ${staging}"
  [[ -n "${out}" ]] || die "export output path required"
}
