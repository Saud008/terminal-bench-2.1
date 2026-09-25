#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"

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

stage=$(cat "${APP_ROOT}/state/kcfg-stage.json")
symbols_json=$(echo "$stage" | jq -c '.after_deps')
violations=$(echo "$stage" | jq -c '.policy_violations')

rows=$(python3 - <<'PY' "$symbols_json"
import json, sys
symbols = json.loads(sys.argv[1])
rows = [{"name": k, "value": v, "source_layer": "stage"} for k, v in sorted(symbols.items())]
print(json.dumps(rows))
PY
)

manifest_digest=$(python3 - <<'PY' "$rows"
import hashlib, json, sys
rows = json.loads(sys.argv[1])
slim = [{"name": r["name"], "value": r["value"], "source_layer": r["source_layer"]} for r in rows]
print(hashlib.sha256(json.dumps(slim, sort_keys=True).encode()).hexdigest())
PY
)

jq -n \
  --arg run_id "$run_id" \
  --argjson symbols "$rows" \
  --argjson policy_violations "$violations" \
  --arg manifest_digest "$manifest_digest" \
  '{run_id: $run_id, symbols: $symbols, policy_violations: $policy_violations, totals: {symbols: ($symbols|length), violations: ($policy_violations|length)}, manifest_digest: $manifest_digest}' \
  > "$output"
echo "manifest written to ${output}"
