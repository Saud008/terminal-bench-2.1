#!/usr/bin/env bash
# Broken: ignores gate file and hook outcomes.

s2_write_staging_manifest() {
  local snap="$1"
  local _gate="$2"
  local hooks_json="$3"
  local resolv_target="$4"
  local sources_digest="$5"
  local out="$6"
  python3 - "$snap" "$hooks_json" "$resolv_target" "$sources_digest" "$out" <<'PY'
import hashlib
import json
import sys

snap = json.load(open(sys.argv[1], encoding="utf-8"))
hooks_doc = json.load(open(sys.argv[2], encoding="utf-8"))
resolv_target = sys.argv[3]
sources_digest = sys.argv[4]
out_path = sys.argv[5]
ids = [row["id"] for row in snap.get("mount_steps", [])]
fp = hashlib.sha256("\n".join(ids).encode()).hexdigest()
binding = hashlib.sha256(json.dumps({"mount_fingerprint": fp, "rootfs": snap["rootfs"], "seed": snap["seed"], "sources_digest": sources_digest}, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
doc = {
    "pipeline_version": 1,
    "snapshot_path": sys.argv[1],
    "seed": snap["seed"],
    "rootfs": snap["rootfs"],
    "mount_count": len(ids),
    "mount_fingerprint": fp,
    "hooks_ok": True,
    "resolv_target": resolv_target,
    "sources_digest": sources_digest,
    "stage_binding": binding,
}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}
