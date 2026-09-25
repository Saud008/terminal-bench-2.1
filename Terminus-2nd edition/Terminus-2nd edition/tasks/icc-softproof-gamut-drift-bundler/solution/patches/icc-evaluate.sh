#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

readings=""
profile=""
paper=""
policy=""
tickets=""
as_of=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --readings) readings="$2"; shift 2 ;;
    --profile) profile="$2"; shift 2 ;;
    --paper) paper="$2"; shift 2 ;;
    --policy) policy="$2"; shift 2 ;;
    --tickets) tickets="$2"; shift 2 ;;
    --as-of) as_of="$2"; shift 2 ;;
    *) source "${APP_ROOT}/lib/common.sh"; die "unknown arg: $1" ;;
  esac
done

source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/staging.sh"

[[ -n "${readings}" && -f "${readings}" ]] || die "evaluate requires readable --readings"
[[ -n "${profile}" && -f "${profile}" ]] || die "evaluate requires readable --profile"
[[ -n "${paper}" && -f "${paper}" ]] || die "evaluate requires readable --paper"
[[ -n "${policy}" && -f "${policy}" ]] || die "evaluate requires readable --policy"
[[ -n "${tickets}" && -f "${tickets}" ]] || die "evaluate requires readable --tickets"
[[ -n "${as_of}" ]] || die "evaluate requires --as-of"

staging="$(stage_path_for "${readings}")"
require_file "${staging}"

evaluate_staging_snapshot "${staging}" "${profile}" "${paper}" "${policy}" "${tickets}" "${as_of}"
echo "evaluate ok: ${staging}"
