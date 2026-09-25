#!/usr/bin/env bash
# Broken: bind mounts sorted before virtual filesystems; ignores devbind-after-proc rule.

s2_compute_mount_order() {
  local rootfs="$1"
  python3 - "$rootfs/mounts.json" <<'PY'
import json
import sys

doc = json.load(open(sys.argv[1], encoding="utf-8"))
mounts = doc["mounts"]
# Wrong: binds first, then virtual, sorted by target string
binds = sorted([m for m in mounts if m.get("kind") == "bind"], key=lambda m: m["target"])
virtual = sorted([m for m in mounts if m.get("kind") != "bind"], key=lambda m: m["id"])
for m in binds + virtual:
    print(m["id"])
PY
}
