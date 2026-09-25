#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/crpe91/export/export_ledger.sh"
run_id=""
pg_start="0"
pg_end="0"
out=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --pg-start) pg_start="$2"; shift 2 ;;
    --pg-end) pg_end="$2"; shift 2 ;;
    --output) out="$2"; shift 2 ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
done
[[ -n "$run_id" && -n "$out" ]] || exit 2
loaded="${APP_ROOT}/work/${run_id}-loaded.json"
[[ -f "$loaded" ]] || exit 2
export_placement_ledger "$loaded" "$run_id" "$pg_start" "$pg_end" "$out"
echo "exported ledger ${run_id}"
