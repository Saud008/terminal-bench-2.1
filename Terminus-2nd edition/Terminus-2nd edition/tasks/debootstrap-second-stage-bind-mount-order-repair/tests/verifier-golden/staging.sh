#!/usr/bin/env bash

s2_write_staging_manifest() {
  local snap="$1"
  local gate="$2"
  local hooks_json="$3"
  local resolv_target="$4"
  local sources_digest="$5"
  local out="$6"
  python3 - "$snap" "$gate" "$hooks_json" "$resolv_target" "$sources_digest" "$out" <<'PY'
import hashlib
import json
import sys

snap_path, gate_path, hooks_path, resolv_target, sources_digest, out_path = sys.argv[1:7]
snap = json.load(open(snap_path, encoding="utf-8"))
gate = json.load(open(gate_path, encoding="utf-8"))
hooks_doc = json.load(open(hooks_path, encoding="utf-8"))
ids = [row["id"] for row in snap.get("mount_steps", [])]
fp = hashlib.sha256("\n".join(ids).encode()).hexdigest()
if gate.get("mount_fingerprint") != fp:
    raise SystemExit("gate mount_fingerprint mismatch")
expected_digest = hashlib.sha256(
    json.dumps(
        {
            "mount_count": len(ids),
            "mount_fingerprint": fp,
            "snapshot_path": snap_path,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
).hexdigest()
if gate.get("gate_digest") != expected_digest:
    raise SystemExit("gate_digest mismatch")
hook_results = hooks_doc.get("hooks", [])
hooks_ok = all(h.get("exit", 1) == 0 for h in hook_results)
binding = hashlib.sha256(
    json.dumps(
        {
            "mount_fingerprint": fp,
            "rootfs": snap["rootfs"],
            "seed": snap["seed"],
            "sources_digest": sources_digest,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
).hexdigest()
doc = {
    "version": 1,
    "snapshot_path": snap_path,
    "gate_path": gate_path,
    "gate_digest": gate["gate_digest"],
    "seed": snap["seed"],
    "rootfs": snap["rootfs"],
    "mount_count": len(ids),
    "mount_fingerprint": fp,
    "hooks_ok": hooks_ok,
    "resolv_target": resolv_target,
    "sources_digest": sources_digest,
    "stage_binding": binding,
}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}
