#!/usr/bin/env bash
set -euo pipefail

scan_policy_violations() {
  local symbols_json="$1"
  local policy_json="$2"
  python3 - <<'PY' "$symbols_json" "$policy_json"
import json, sys

symbols = json.loads(sys.argv[1])
policy = json.loads(sys.argv[2])
violations = []
for sym in policy.get("forbidden_if_set", []):
    if symbols.get(sym) == "y":
        violations.append({"symbol": sym, "code": "forbidden_set", "detail": "symbol must not be enabled"})
for sym in policy.get("required_n", []):
    val = symbols.get(sym)
    if val not in (None, "n"):
        violations.append({"symbol": sym, "code": "required_n", "detail": "symbol must be disabled"})
for sym in policy.get("max_modular", []):
    if symbols.get(sym) == "y":
        violations.append({"symbol": sym, "code": "max_modular", "detail": "symbol must be modular or disabled"})
violations.sort(key=lambda v: v["symbol"])
print(json.dumps(violations))
PY
}
