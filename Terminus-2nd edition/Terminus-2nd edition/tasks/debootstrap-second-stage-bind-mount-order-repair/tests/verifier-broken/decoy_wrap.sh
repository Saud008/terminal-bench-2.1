#!/usr/bin/env bash
# Decoy: lexicographic target sort — not used by stage2-audit hot path but looks like the mount fix.

s2_sort_mounts_by_target() {
  local rootfs="$1"
  python3 - "$rootfs/mounts.json" <<'PY'
import json
import sys

doc = json.load(open(sys.argv[1], encoding="utf-8"))
for m in sorted(doc["mounts"], key=lambda row: row["target"]):
    print(m["id"])
PY
}
