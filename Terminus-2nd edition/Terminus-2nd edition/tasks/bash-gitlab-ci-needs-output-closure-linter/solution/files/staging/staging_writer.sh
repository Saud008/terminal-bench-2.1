#!/usr/bin/env bash
# Staging digest covers run_id, active job shape, and rules fingerprint.
set -euo pipefail

staging_digest() {
  local body_json="$1"
  python3 - <<'PY' "$body_json"
import hashlib, json, sys
body = json.loads(sys.argv[1])
slim = {
    "run_id": body["run_id"],
    "jobs": [{"name": j["name"], "stage": j["stage"], "active": j["active"]} for j in body["jobs"]],
    "rules_fingerprint": body.get("rules_fingerprint", ""),
}
print(hashlib.sha256(json.dumps(slim, sort_keys=True).encode()).hexdigest())
PY
}
