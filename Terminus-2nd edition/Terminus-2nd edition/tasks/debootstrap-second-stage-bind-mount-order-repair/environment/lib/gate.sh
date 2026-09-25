#!/usr/bin/env bash
# Broken: gate_digest ignores mount_count and never validates DAG.

s2_write_mount_gate() {
  local snap="$1"
  local out="$2"
  python3 - "$snap" "$out" <<'PY'
import hashlib
import json
import sys

snap = json.load(open(sys.argv[1], encoding="utf-8"))
ids = [row["id"] for row in snap.get("mount_steps", [])]
fp = hashlib.sha256("\n".join(ids).encode()).hexdigest()
digest = hashlib.sha256(fp.encode()).hexdigest()
doc = {
    "pipeline_version": 1,
    "snapshot_path": sys.argv[1],
    "mount_fingerprint": fp,
    "mount_count": len(ids),
    "gate_digest": digest,
}
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}
