#!/usr/bin/env bash
# Build restore planner JSON from staging snapshot.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/continuity.sh"
source "${APP_ROOT}/lib/partial.sh"
source "${APP_ROOT}/lib/target.sh"

write_restore_plan() {
  local staging_path="$1"
  local out_path="$2"
  local restore_target="$3"
  local config_root="${4:-/app/config}"
  python3 - "${staging_path}" "${out_path}" "${restore_target}" "${config_root}" <<'PY'
import json, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

def parse_utc(text):
    return datetime.strptime(text.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

def fmt(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

stage = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(sys.argv[2])
restore_target = sys.argv[3]
config_root = Path(sys.argv[4])
clock = json.loads((config_root / "segment-clock.json").read_text(encoding="utf-8"))
seconds = int(clock["seconds_per_segment"])
base = parse_utc(stage["start_time"])
target = parse_utc(restore_target)
selected = None
best = None
for name in stage["segments_present"]:
    seg = int(name[8:24], 16)
    end = base + timedelta(seconds=seg * seconds)
    if end <= target and (best is None or end > best):
        selected = name
        best = end
by = {}
for name in stage["segments_present"]:
    tl = int(name[0:8], 16)
    seg = int(name[8:24], 16)
    by.setdefault(tl, []).append(seg)
gaps = []
for tl in sorted(by):
    nums = sorted(by[tl])
    for prev, cur in zip(nums, nums[1:]):
        if cur != prev + 1:
            gaps.append({"timeline": tl, "from_segment": f"{tl:08X}{prev:016X}", "to_segment": f"{tl:08X}{cur:016X}"})
continuity_ok = len(gaps) == 0
partial_rejected = []
if selected:
    sel_tl = int(selected[0:8], 16)
    sel_seg = int(selected[8:24], 16)
    for name in stage.get("partial_files", []):
        base_name = name[:-8] if name.endswith(".partial") else name
        tl = int(base_name[0:8], 16)
        seg = int(base_name[8:24], 16)
        if tl == sel_tl and seg <= sel_seg:
            partial_rejected.append(name)
restore_ready = continuity_ok and selected is not None and len(partial_rejected) == 0
plan = {
    "schema": "pg-wal-restore-plan/1",
    "archive_root": stage["archive_root"],
    "staging_version": stage["staging_version"],
    "restore_ready": restore_ready,
    "restore_target_time": fmt(target),
    "target_timeline": int(selected[0:8], 16) if selected else stage["start_timeline"],
    "selected_segment": selected,
    "continuity_ok": continuity_ok,
    "gaps": gaps,
    "partial_rejected": partial_rejected,
    "digest": stage["digest"],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("0" if restore_ready else "2")
PY
}
