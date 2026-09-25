#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
pair_id=""
output=""
args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --pair) pair_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) args+=("$1"); shift ;;
  esac
done
exec python3 "${APP_ROOT}/lib/risk_engine.py" export --pair-id "${pair_id}" --output "${output}" "${args[@]}"
