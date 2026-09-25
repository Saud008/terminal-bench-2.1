#!/usr/bin/env bash

s2_write_mount_snapshot() {
  local rootfs="$1"
  local out="$2"
  python3 - "$rootfs" "$out" "$S2_META_SEED" "$S2_META_ROOTFS" <<'PY'
import json
import subprocess
import sys

rootfs, out_path, seed, name = sys.argv[1:5]
order = subprocess.check_output(
    ["bash", "-c", f"source /app/lib/mount.sh && s2_compute_mount_order {rootfs}"],
    text=True,
).splitlines()
mounts = {m["id"]: m for m in json.load(open(f"{rootfs}/mounts.json", encoding="utf-8"))["mounts"]}
steps = []
for mid in order:
    m = mounts[mid]
    steps.append(
        {
            "id": m["id"],
            "source": m["source"],
            "target": m["target"],
            "fstype": m["fstype"],
            "kind": m["kind"],
            "options": m.get("options", []),
        }
    )
doc = {"version": 1, "seed": seed, "rootfs": name, "mount_steps": steps}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY
}
