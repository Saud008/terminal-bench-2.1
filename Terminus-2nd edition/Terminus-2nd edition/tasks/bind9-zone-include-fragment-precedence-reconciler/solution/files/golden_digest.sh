#!/usr/bin/env bash

canonical_snapshot_digest() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import hashlib, json, sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
payload = {
    "origin": meta.get("origin"),
    "processing_order": meta.get("processing_order"),
    "records": meta.get("records"),
    "soa_serial": meta.get("soa_serial"),
    "include_fingerprint": meta.get("include_fingerprint"),
}
digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
print(digest)
PY
}

legacy_effective_digest() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import hashlib, json, sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
keys = sorted(r["owner"] + "/" + r["type"] for r in meta.get("records", []))
print(hashlib.sha256("|".join(keys).encode()).hexdigest())
PY
}
