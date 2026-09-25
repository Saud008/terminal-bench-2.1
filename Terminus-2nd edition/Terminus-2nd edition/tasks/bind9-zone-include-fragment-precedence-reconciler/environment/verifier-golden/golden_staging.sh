#!/usr/bin/env bash

write_merge_staging() {
  local snap="$1"
  local digest
  digest="$(canonical_snapshot_digest "$snap")"
  python3 - "$snap" "$digest" <<'PY'
import json, sys
from pathlib import Path

snap = Path(sys.argv[1])
digest = sys.argv[2]
meta = json.loads(snap.read_text(encoding="utf-8"))
staging = {
    "staging_version": 1,
    "snapshot_digest": digest,
    "processing_order": meta.get("processing_order", []),
    "record_count": len(meta.get("records", [])),
}
staging_path = snap.with_suffix(snap.suffix + ".merge-staging.json")
staging_path.write_text(json.dumps(staging, indent=2) + "\n", encoding="utf-8")
PY
}

validate_merge_staging() {
  local snap="$1"
  local digest
  digest="$(canonical_snapshot_digest "$snap")"
  python3 - "$snap" "$digest" <<'PY'
import json, sys
from pathlib import Path

snap = Path(sys.argv[1])
expected = sys.argv[2]
staging_path = snap.with_suffix(snap.suffix + ".merge-staging.json")
if not staging_path.is_file():
    sys.exit(4)
staging = json.loads(staging_path.read_text(encoding="utf-8"))
if staging.get("snapshot_digest") != expected:
    sys.exit(4)
sys.exit(0)
PY
}
