#!/usr/bin/env bash
set -euo pipefail

staging_digest() {
  local body_json="$1"
  python3 - <<'PY' "$body_json"
import hashlib, json, sys
body = json.loads(sys.argv[1])
slim = {
    "run_id": body["run_id"],
    "source_fingerprint": body.get("source_fingerprint", ""),
    "packages": [{"name": p["package"], "version": p["version"], "source_id": p.get("source_id", "")} for p in body["packages"]],
}
print(hashlib.sha256(json.dumps(slim, sort_keys=True).encode()).hexdigest())
PY
}
