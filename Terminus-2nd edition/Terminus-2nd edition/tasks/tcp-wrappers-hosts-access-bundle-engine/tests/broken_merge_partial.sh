#!/usr/bin/env bash
# Partial fix: allow-before-deny export order but swapped stats counts.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=parse.sh
source "$(dirname "${BASH_SOURCE[0]}")/parse.sh"

merge_bundle() {
  local root="$1"
  local export_path="$2"
  local manifest name rules_json
  manifest="$(read_manifest "$root")"
  name="$(python3 - "$manifest" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["name"])
PY
)"
  rules_json="$(load_bundle_rules "$root")"
  payload="$(python3 - "$name" "$rules_json" <<'PY'
import json, sys
name, rules = sys.argv[1], json.loads(sys.argv[2])
allow = [r for r in rules if r["side"] == "allow"]
deny = [r for r in rules if r["side"] == "deny"]
merged = allow + deny
for idx, rule in enumerate(merged):
    rule["index"] = idx
print(json.dumps({
    "bundle": name,
    "rules": merged,
    "stats": {
        "allow_rules": len(deny),
        "deny_rules": len(allow),
        "total_rules": len(merged),
    },
}, indent=2))
PY
)"
  json_write "$export_path" "$payload"
}
