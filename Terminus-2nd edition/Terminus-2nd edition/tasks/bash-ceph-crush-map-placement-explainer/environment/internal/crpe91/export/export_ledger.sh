#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/internal/crpe91/trace/trace_pg.sh"
source "${APP_ROOT}/internal/crpe91/workspace/normalized_fingerprint.sh"

export_placement_ledger() {
  local loaded="$1"
  local run_id="$2"
  local pg_start="$3"
  local pg_end="$4"
  local out="$5"
  local pool pg traces="[]"
  pool=$(jq -c '.pool' "$loaded")
  fp=$(normalized_fingerprint "$loaded")
  for pg in $(seq "$pg_start" "$pg_end"); do
    row=$(trace_pg_placement "$loaded" "$pg")
    traces=$(echo "$traces" | jq --argjson r "$row" '. + [$r]')
  done
  traces=$(echo "$traces" | jq 'sort_by(.pg_num) | reverse')
  map_name=$(jq -r '.map_name' "$loaded")
  pool_name=$(echo "$pool" | jq -r '.name')
  pool_id=$(echo "$pool" | jq -r '.id')
  digest=$(echo "$traces" | jq -c --arg rid "$run_id" --argjson pid "$pool_id" \
    '{run_id: $rid, pool_id: $pid, pg_traces: [.[] | {pg_id, acting_set, primary_osd}]}' \
    | sha256sum | awk '{print $1}')
  jq -n --arg run_id "$run_id" --arg map_name "$map_name" --arg pool "$pool_name" \
    --argjson pool_id "$pool_id" --arg fp "$fp" --argjson traces "$traces" --arg digest "$digest" \
    '{run_id: $run_id, map_name: $map_name, pool: $pool, pool_id: $pool_id, normalized_fingerprint: $fp, pg_traces: $traces, ledger_digest: $digest}' \
    > "$out"
}
