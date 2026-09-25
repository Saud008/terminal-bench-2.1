#!/usr/bin/env bash
checker_gate() {
  local board_jsonl="$1"
  local capture_id="$2"
  local limit="$3"
  python3 - "$board_jsonl" "$capture_id" "$limit" <<'PY'
import json, sys
path, cap_id, limit = sys.argv[1], sys.argv[2], float(sys.argv[3])
for line in open(path, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    row = json.loads(line)
    if row.get("capture_id") != cap_id:
        continue
    if not row.get("board_detected", True):
        print("calibration_failed")
        raise SystemExit(0)
    if float(row.get("reprojection_error", 0)) > limit:
        print("calibration_failed")
        raise SystemExit(0)
    print("ok")
    raise SystemExit(0)
print("ok")
PY
}
