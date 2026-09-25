#!/usr/bin/env bash
compute_missing_frames() {
  local mount_json="$1"
  local accepted_json="$2"
  python3 - "$mount_json" "$accepted_json" <<'PY'
import json, sys
mount = json.loads(open(sys.argv[1], encoding="utf-8").read())
accepted = json.loads(sys.argv[2])
start = int(mount.get("frame_index_start", 1))
count = int(mount.get("expected_frames_per_slot", 0))
expected = set(range(start, start + count - 1))
by_slot = {}
for row in accepted:
    slot = int(row["rig_slot"])
    by_slot.setdefault(slot, set()).add(int(row["frame_index"]))
missing = []
for slot_row in mount.get("slots", []):
    slot = int(slot_row["slot"])
    seen = by_slot.get(slot, set())
    for idx in sorted(expected - seen):
        missing.append({"rig_slot": slot, "frame_index": idx})
print(json.dumps(missing, separators=(",", ":")))
PY
}
