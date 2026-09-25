#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"
source "$(dirname "${BASH_SOURCE[0]}")/../ledger/ledger_build.sh"

run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$run_id" ]] || { echo "missing --run-id" >&2; exit 2; }

load="${WORK_DIR}/${run_id}-load.json"
[[ -f "$load" ]] || { echo "missing load" >&2; exit 2; }

build_ledger "$run_id" "$load" >"$LEDGER"
echo "$LEDGER"
