#!/usr/bin/env bash
# Partial-fix profile: correct allow-before-deny merge wired through staging/publish.

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
        "allow_rules": len(allow),
        "deny_rules": len(deny),
        "total_rules": len(merged),
    },
}, indent=2))
PY
)"
  fp="$(bundle_fingerprint "$root")"
  write_merge_staging "$name" "$payload"
  publish_from_staging "$name" "$fp" "$export_path" "$payload"
}
