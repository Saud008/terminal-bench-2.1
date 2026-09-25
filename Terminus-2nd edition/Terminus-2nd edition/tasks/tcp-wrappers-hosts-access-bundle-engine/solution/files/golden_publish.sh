#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

staging_path() {
  local bundle_name="$1"
  printf '%s/work/staging/%s.json' "$APP_ROOT" "$bundle_name"
}

compute_publish_seal() {
  local merged_json="$1"
  python3 - "$merged_json" <<'PY'
import hashlib
import json
import sys

merged = json.loads(sys.argv[1])
rules = merged["rules"]
stats = merged["stats"]
first_deny = next((i for i, r in enumerate(rules) if r["side"] == "deny"), len(rules))
body = json.dumps(
    {
        "allow_rules": stats["allow_rules"],
        "deny_rules": stats["deny_rules"],
        "total_rules": stats["total_rules"],
        "first_deny_index": first_deny,
        "sides": [r["side"] for r in rules],
    },
    sort_keys=True,
    separators=(",", ":"),
)
print(hashlib.sha256(body.encode("utf-8")).hexdigest())
PY
}

write_merge_staging() {
  local bundle_name="$1"
  local merged_json="$2"
  local staging seal
  staging="$(staging_path "$bundle_name")"
  seal="$(compute_publish_seal "$merged_json")"
  mkdir -p "$(dirname "$staging")"
  python3 - "$bundle_name" "$merged_json" "$seal" "$staging" <<'PY'
import json, sys

bundle, merged_json, seal, out = sys.argv[1:5]
payload = {
    "bundle": bundle,
    "merged": json.loads(merged_json),
    "publish_seal": seal,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=2)
    fh.write("\n")
PY
}

publish_from_staging() {
  local bundle_name="$1"
  local fingerprint="$2"
  local export_path="$3"
  local merged_json="$4"
  local staging stored want
  staging="$(staging_path "$bundle_name")"
  [[ -f "$staging" ]] || die "missing staging for $bundle_name"
  want="$(compute_publish_seal "$merged_json")"
  stored="$(python3 - "$staging" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8")).get("publish_seal", ""))
PY
)"
  [[ "$stored" == "$want" ]] || die "staging publish_seal mismatch for $bundle_name"
  write_merge_cache "$bundle_name" "$fingerprint" "$merged_json" "$want"
  if [[ -n "$export_path" ]]; then
    json_write "$export_path" "$merged_json"
  fi
}
