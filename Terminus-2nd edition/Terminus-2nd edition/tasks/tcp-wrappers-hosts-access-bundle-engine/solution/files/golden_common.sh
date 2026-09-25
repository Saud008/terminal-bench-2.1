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
  local manifest
  manifest="$(read_manifest "$root")"
  python3 - "$root" "$manifest" <<'PY'
import hashlib
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1])
manifest = json.loads(sys.argv[2])
h = hashlib.sha256()
for rel in manifest.get("allow_files", []) + manifest.get("deny_files", []):
    path = root / rel
    h.update(rel.encode("utf-8"))
    h.update(b"\n")
    h.update(path.read_bytes())
    h.update(b"\n")
h.update((root / "manifest.json").read_bytes())
print(h.hexdigest())
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
  local publish_seal="${4:-}"
  local cache_path
  cache_path="$(merge_cache_path "$bundle_name")"
  mkdir -p "$(dirname "$cache_path")"
  python3 - "$fingerprint" "$publish_seal" "$merged_json" "$cache_path" <<'PY'
import json, sys

fp, seal, merged_json, out = sys.argv[1:5]
merged = json.loads(merged_json)
payload = {"fingerprint": fp, "publish_seal": seal, "merged": merged}
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
  local fp cache_json
  fp="$(bundle_fingerprint "$root")"
  cache_json="$(read_merge_cache "$bundle_name" || true)"
  [[ -n "$cache_json" ]] || return 1
  HOSTSCTL_LIB="${HOSTSCTL_LIB}" python3 - "$fp" "$cache_json" <<'PY'
import hashlib
import json
import sys

want_fp, cache = sys.argv[1], json.loads(sys.argv[2])
if cache.get("fingerprint") != want_fp:
    raise SystemExit(1)
merged = cache["merged"]
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
want_seal = hashlib.sha256(body.encode("utf-8")).hexdigest()
if cache.get("publish_seal") != want_seal:
    raise SystemExit(1)
print(json.dumps(rules))
PY
}
