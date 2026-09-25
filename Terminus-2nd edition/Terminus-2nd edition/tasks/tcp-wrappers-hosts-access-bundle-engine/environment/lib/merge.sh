#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"
# shellcheck source=parse.sh
source "$(dirname "${BASH_SOURCE[0]}")/parse.sh"
# shellcheck source=publish.sh
source "$(dirname "${BASH_SOURCE[0]}")/publish.sh"

merge_bundle() {
  local root="$1"
  local export_path="$2"
  local manifest name rules_json payload fp
  manifest="$(read_manifest "$root")"
  name="$(python3 - "$manifest" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["name"])
PY
)"
  rules_json="$(load_bundle_rules "$root")"
  fp="$(bundle_fingerprint "$root")"
  payload="$(python3 - "$name" "$rules_json" <<'PY'
import json, sys
name, rules = sys.argv[1], json.loads(sys.argv[2])
deny = [r for r in rules if r["side"] == "deny"]
allow = [r for r in rules if r["side"] == "allow"]
merged = deny + allow
for idx, rule in enumerate(merged):
    rule["index"] = idx
print(json.dumps({
    "bundle": name,
    "rules": merged,
    "stats": {
        "allow_rules": sum(1 for r in merged if r["side"] == "allow"),
        "deny_rules": sum(1 for r in merged if r["side"] == "deny"),
        "total_rules": len(merged),
    },
}, indent=2))
PY
)"
  write_merge_staging "$name" "$payload"
  publish_from_staging "$name" "$fp" "$export_path" "$payload"
}
