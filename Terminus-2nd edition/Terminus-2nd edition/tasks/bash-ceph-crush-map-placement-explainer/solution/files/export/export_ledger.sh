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
  traces=$(echo "$traces" | jq 'sort_by(.pg_num)')
  map_name=$(jq -r '.map_name' "$loaded")
  pool_name=$(echo "$pool" | jq -r '.name')
  pool_id=$(echo "$pool" | jq -r '.id')
  digest=$(python3 - <<'PY' "$run_id" "$pool_id" "$traces"
import hashlib, json, sys
run_id = sys.argv[1]
pool_id = int(sys.argv[2])
traces = json.loads(sys.argv[3])
body = {
    "run_id": run_id,
    "pool_id": pool_id,
    "pg_traces": [
        {"pg_id": t["pg_id"], "acting_set": t["acting_set"], "primary_osd": t["primary_osd"]}
        for t in traces
    ],
}
print(hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest())
PY
)
  jq -n --arg run_id "$run_id" --arg map_name "$map_name" --arg pool "$pool_name" \
    --argjson pool_id "$pool_id" --arg fp "$fp" --argjson traces "$traces" --arg digest "$digest" \
    '{run_id: $run_id, map_name: $map_name, pool: $pool, pool_id: $pool_id, normalized_fingerprint: $fp, pg_traces: $traces, ledger_digest: $digest}' \
    > "$out"
}
