#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="/app"
source "${APP_ROOT}/lib/attpipe/p01.sh"
source "${APP_ROOT}/lib/attpipe/p03.sh"
source "${APP_ROOT}/lib/attpipe/p04.sh"
source "${APP_ROOT}/lib/attpipe/p05.sh"

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
bundle=$(echo "$stage" | jq -r '.bundle')
base="${APP_ROOT}/fixtures/bundles/${bundle}"
symbols=$(merge_layers "${base}/defconfig" "${base}/fragments")
symbols=$(apply_deps_closure "$symbols" "$(cat "${base}/deps.json")")
violations=$(scan_policy_violations "$symbols" "$(cat "${base}/policy.json")")

rows=$(python3 - <<'PY' "$symbols"
import json, sys
symbols = json.loads(sys.argv[1])
rows = [{"name": k, "value": v, "source_layer": "merged"} for k, v in sorted(symbols.items())]
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
