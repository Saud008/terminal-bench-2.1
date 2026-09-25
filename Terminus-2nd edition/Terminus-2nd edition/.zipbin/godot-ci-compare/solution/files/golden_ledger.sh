#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_build_ledger() {
  local merged_json="$1"
  python3 - "${merged_json}" <<'PY'
import hashlib, json, sys

def norm(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")

def canonicalize(value):
    if isinstance(value, dict):
        return {k: canonicalize(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [canonicalize(v) for v in value]
    return value

merged = json.loads(sys.argv[1])
entries = []
for path in sorted(merged.keys()):
    normalized = norm(merged[path])
    entries.append({
        "path": path,
        "content_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
    })
body = {"entries": entries}
checksum = hashlib.sha256(
    json.dumps(canonicalize(body), sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
body["checksum"] = checksum
print(json.dumps(body))
PY
}
