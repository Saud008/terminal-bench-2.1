#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
# Export reads ingest work artifacts for findings assembly.
source "${APP_ROOT}/internal/pk87/needs/stage_order.sh"
source "${APP_ROOT}/internal/pk87/needs/needs_graph.sh"
source "${APP_ROOT}/internal/pk87/needs/artifact_closure.sh"

run_id=""
output=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    --output) output="$2"; shift 2 ;;
    *) exit 2 ;;
  esac
done
[[ -n "$run_id" && -n "$output" ]] || exit 2

pipeline=$(cat "${APP_ROOT}/work/${run_id}-ingest.json")
stages=$(echo "$pipeline" | jq -c '.stages // []')
findings="[]"
summary='{"error":0,"warn":0,"info":0}'

jq -n --arg run_id "$run_id" --argjson findings "$findings" --argjson summary "$summary" \
  '{run_id: $run_id, findings: $findings, summary: $summary, audit_digest: "broken"}' > "$output"
