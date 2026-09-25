#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export HOSTSCTL_LIB="${HOSTSCTL_LIB:-${LIB_DIR}}"

die() {
  echo "hostsctl error: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing command: $1"
}

# Note: json_write runs in the current shell; it resets $? on success. Wrappers that
# run a Python checker via command substitution must save rc before calling json_write.
json_write() {
  local path="$1"
  local payload="$2"
  mkdir -p "$(dirname "$path")"
  printf '%s\n' "$payload" >"$path"
}

bundle_root() {
  local bundle="$1"
  if [[ -f "${bundle}/manifest.json" ]]; then
    printf '%s' "${bundle%/}"
    return 0
  fi
  if [[ -f "${APP_ROOT}/fixtures/bundles/${bundle}/manifest.json" ]]; then
    printf '%s' "${APP_ROOT}/fixtures/bundles/${bundle}"
    return 0
  fi
  die "bundle not found: $bundle"
}

read_manifest() {
  local root="$1"
  python3 - "$root/manifest.json" <<'PY'
import json, sys
print(json.dumps(json.load(open(sys.argv[1], encoding="utf-8"))))
PY
}

bundle_fingerprint() {
  local root="$1"
  python3 - "$root/manifest.json" <<'PY'
import hashlib, sys
print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())
PY
}

merge_cache_path() {
  local bundle_name="$1"
  printf '%s/work/merged/%s.json' "$APP_ROOT" "$bundle_name"
}

write_merge_cache() {
  local bundle_name="$1"
  local fingerprint="$2"
  local merged_json="$3"
  local cache_path
  cache_path="$(merge_cache_path "$bundle_name")"
  mkdir -p "$(dirname "$cache_path")"
  python3 - "$fingerprint" "$merged_json" "$cache_path" <<'PY'
import json, sys
fp, merged_json, out = sys.argv[1:4]
merged = json.loads(merged_json)
payload = {"fingerprint": fp, "merged": merged}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, indent=2)
    fh.write("\n")
PY
}

read_merge_cache() {
  local bundle_name="$1"
  local cache_path
  cache_path="$(merge_cache_path "$bundle_name")"
  [[ -f "$cache_path" ]] || return 1
  python3 - "$cache_path" <<'PY'
import json, sys
print(json.dumps(json.load(open(sys.argv[1], encoding="utf-8"))))
PY
}

load_cached_rules() {
  local root="$1"
  local bundle_name="$2"
  local cache_json
  cache_json="$(read_merge_cache "$bundle_name" || true)"
  [[ -n "$cache_json" ]] || return 1
  python3 - "$cache_json" <<'PY'
import json, sys
print(json.dumps(json.loads(sys.argv[1])["merged"]["rules"]))
PY
}
