#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/crpe91/parse/load_map.sh"
map=""
run_id=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --map) map="$2"; shift 2 ;;
    --run-id) run_id="$2"; shift 2 ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
done
[[ -n "$map" && -n "$run_id" ]] || exit 2
root="${TB3_MAP_ROOT:-${APP_ROOT}/maps}"
load_crush_bundle "${root}/${map}" "${APP_ROOT}/work/${run_id}-loaded.json"
echo "loaded ${map} for ${run_id}"
