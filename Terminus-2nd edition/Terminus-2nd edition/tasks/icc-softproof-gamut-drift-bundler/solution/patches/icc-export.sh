#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

readings=""
out="/app/output/drift-report.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --readings) readings="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) source "${APP_ROOT}/lib/common.sh"; die "unknown arg: $1" ;;
  esac
done

source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/export_report.sh"

[[ -n "${readings}" && -f "${readings}" ]] || die "export requires readable --readings"
[[ -n "${out}" ]] || die "export requires --out"

staging="$(stage_path_for "${readings}")"
require_file "${staging}"
if [[ -x "${APP_ROOT}/stage/validate-staging.sh" ]]; then
  # shellcheck source=/dev/null
  source "${APP_ROOT}/stage/validate-staging.sh"
  validate_staging_file "${staging}"
fi

if ! jq -e '.evaluation' "${staging}" >/dev/null 2>&1; then
  die "staging missing evaluation block; run evaluate first"
fi

drift_count="$(write_drift_report "${staging}" "${out}")"
if [[ "${drift_count}" -gt 0 ]]; then
  exit 2
fi
echo "export ok: ${out}"
