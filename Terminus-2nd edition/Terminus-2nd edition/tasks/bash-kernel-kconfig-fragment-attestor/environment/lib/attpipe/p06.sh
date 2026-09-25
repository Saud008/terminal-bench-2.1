#!/usr/bin/env bash
set -euo pipefail

stage_digest() {
  local run_id="$1"
  local bundle="$2"
  local frag_order_json="$3"
  local symbols_json="$4"
  python3 - <<'PY' "$run_id" "$bundle" "$frag_order_json" "$symbols_json"
import hashlib, json, sys

run_id, bundle = sys.argv[1], sys.argv[2]
frag_order = json.loads(sys.argv[3])
symbols = json.loads(sys.argv[4])
body = {
    "run_id": run_id,
    "bundle": bundle,
    "fragment_order": frag_order,
    "symbol_count": len(symbols),
}
print(hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest())
PY
}
