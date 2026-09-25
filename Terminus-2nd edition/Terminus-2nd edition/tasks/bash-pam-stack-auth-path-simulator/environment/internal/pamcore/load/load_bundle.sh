#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"

scenario=""
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) scenario="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$scenario" && -n "$run_id" ]] || { echo "missing flags" >&2; exit 2; }

root="${SCENARIO_DIR}/${scenario}"
[[ -d "$root" ]] || { echo "scenario missing" >&2; exit 2; }

mkdir -p "$WORK_DIR"
out="${WORK_DIR}/${run_id}-load.json"
jq -n --arg s "$scenario" --arg r "$run_id" --arg root "$root"           '{scenario:$s, run_id:$r, scenario_root:$root}' >"$out"
echo "$out"
