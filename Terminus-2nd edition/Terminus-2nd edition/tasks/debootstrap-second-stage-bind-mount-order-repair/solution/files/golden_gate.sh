#!/usr/bin/env bash

s2_write_mount_gate() {
  local snap="$1"
  local out="$2"
  python3 - "$snap" "$out" <<'PY'
import hashlib
import json
import sys

snap_path, out_path = sys.argv[1:3]
snap = json.load(open(snap_path, encoding="utf-8"))
ids = [row["id"] for row in snap.get("mount_steps", [])]
fp = hashlib.sha256("\n".join(ids).encode()).hexdigest()
mount_count = len(ids)
payload = {
    "mount_count": mount_count,
    "mount_fingerprint": fp,
    "snapshot_path": snap_path,
}
digest = hashlib.sha256(
    json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
doc = {
    "version": 1,
    "snapshot_path": snap_path,
    "mount_fingerprint": fp,
    "mount_count": mount_count,
    "gate_digest": digest,
}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}
