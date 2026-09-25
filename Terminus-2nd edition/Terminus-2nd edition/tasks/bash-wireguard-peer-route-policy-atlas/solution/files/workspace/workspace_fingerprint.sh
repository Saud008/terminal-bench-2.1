#!/usr/bin/env bash
set -euo pipefail

workspace_fingerprint() {
  local body_json="$1"
  python3 - <<'PY' "$body_json"
import hashlib, json, sys
body = json.loads(sys.argv[1])
fp_body = {
    "run_id": body["run_id"],
    "peers": [
        {"public_key": p["public_key"], "allowed_ips": p["allowed_ips"], "disabled": p.get("disabled", False)}
        for p in body.get("peers", [])
    ],
    "overlaps": body.get("overlaps", []),
    "disabled_skipped": body.get("disabled_skipped", []),
}
print(hashlib.sha256(json.dumps(fp_body, sort_keys=True).encode()).hexdigest())
PY
}
