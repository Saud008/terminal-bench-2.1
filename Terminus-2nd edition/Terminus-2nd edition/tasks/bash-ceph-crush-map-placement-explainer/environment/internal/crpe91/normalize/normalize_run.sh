#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/crpe91/workspace/normalized_fingerprint.sh"
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
done
[[ -n "$run_id" ]] || exit 2
loaded="${APP_ROOT}/work/${run_id}-loaded.json"
[[ -f "$loaded" ]] || exit 2
fp=$(normalized_fingerprint "$loaded")
jq --arg fp "$fp" --arg run_id "$run_id" '. + {run_id: $run_id, normalized_fingerprint: $fp}' "$loaded" \
  > "${APP_ROOT}/state/crpe-normalized.json"
echo "normalized ${run_id}"
