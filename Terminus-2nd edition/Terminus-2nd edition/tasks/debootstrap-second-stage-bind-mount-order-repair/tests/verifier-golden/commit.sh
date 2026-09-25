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

s2_apply_mount_markers() {
  local rootfs="$1"
  local snap="$2"
  python3 - "$rootfs" "$snap" <<'PY'
import json
import pathlib
import sys

rootfs, snap_path = sys.argv[1:3]
snap = json.load(open(snap_path, encoding="utf-8"))
tree = pathlib.Path(rootfs) / "tree"
mounted: list[str] = []
for row in snap.get("mount_steps", []):
    mid = row["id"]
    mounted.append(mid)
    if mid == "proc":
        p = tree / "proc"
        p.mkdir(parents=True, exist_ok=True)
        (p / ".stage2-proc-ready").write_text("ok\n", encoding="utf-8")
    if mid == "devbind" and "proc" in mounted:
        p = tree / "dev"
        p.mkdir(parents=True, exist_ok=True)
        (p / ".stage2-dev-ready").write_text("ok\n", encoding="utf-8")
PY
}
