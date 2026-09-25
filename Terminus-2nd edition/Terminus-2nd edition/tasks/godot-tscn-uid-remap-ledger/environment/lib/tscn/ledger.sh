#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_build_ledger() {
  local merged_json="$1"
  python3 - "${merged_json}" <<'PY'
import hashlib, json, sys

merged = json.loads(sys.argv[1])
entries = []
for path in sorted(merged.keys()):
    raw = merged[path].encode("utf-8")
    entries.append({
        "path": path,
        "content_sha256": hashlib.sha256(raw).hexdigest(),
    })
body = {"entries": entries}
canonical = json.dumps(body, sort_keys=True, separators=(",", ":"))
body["checksum"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
print(json.dumps(body))
PY
}
