#!/usr/bin/env bash
set -euo pipefail

normalized_fingerprint() {
  local loaded="$1"
  python3 - <<'PY' "$loaded"
import hashlib, json, sys
loaded = json.loads(open(sys.argv[1]).read())
body = {"map": loaded.get("map_name"), "osds": loaded["osd"]["osds"]}
print(hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest())
PY
}
