#!/usr/bin/env bash

# Oracle golden: full snapshot binding (same payload as canonical_snapshot_digest).
legacy_staging_digest() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import hashlib, json, sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
payload = {
    "processing_order": meta["processing_order"],
    "effective": meta["effective"],
    "sources": meta["sources"],
}
digest = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
).hexdigest()
print(digest)
PY
}
