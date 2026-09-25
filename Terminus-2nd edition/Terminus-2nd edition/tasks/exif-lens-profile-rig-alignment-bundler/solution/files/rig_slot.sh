#!/usr/bin/env bash
validate_rig_slot() {
  local mount_json="$1"
  local rig_slot="$2"
  local camera_serial="$3"
  local lens_id="$4"
  python3 - "$mount_json" "$rig_slot" "$camera_serial" "$lens_id" <<'PY'
import json, sys
mount, slot_s, serial, lens = sys.argv[1:5]
slot = int(slot_s)
data = json.loads(open(mount, encoding="utf-8").read())
for row in data.get("slots", []):
    if int(row["slot"]) != slot:
        continue
    if row.get("camera_serial") != serial:
        print("rig_slot_mismatch")
        raise SystemExit(0)
    allowed = row.get("allowed_lens_ids") or []
    if lens not in allowed:
        print("lens_not_allowed")
        raise SystemExit(0)
    print("ok")
    raise SystemExit(0)
print("rig_slot_mismatch")
PY
}
