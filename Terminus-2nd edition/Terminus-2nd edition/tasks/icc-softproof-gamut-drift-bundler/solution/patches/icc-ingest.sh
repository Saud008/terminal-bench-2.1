#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

readings=""
profile=""
paper=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --readings) readings="$2"; shift 2 ;;
    --profile) profile="$2"; shift 2 ;;
    --paper) paper="$2"; shift 2 ;;
    *) source "${APP_ROOT}/lib/common.sh"; die "unknown arg: $1" ;;
  esac
done

source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/staging.sh"

[[ -n "${readings}" && -f "${readings}" ]] || die "ingest requires readable --readings"
[[ -n "${profile}" && -f "${profile}" ]] || die "ingest requires readable --profile"
[[ -n "${paper}" && -f "${paper}" ]] || die "ingest requires readable --paper"

staging="$(stage_path_for "${readings}")"
write_staging_snapshot "${readings}" "${profile}" "${paper}" "${staging}"
update_run_registry "${readings}"
echo "ingest ok: ${staging}"
