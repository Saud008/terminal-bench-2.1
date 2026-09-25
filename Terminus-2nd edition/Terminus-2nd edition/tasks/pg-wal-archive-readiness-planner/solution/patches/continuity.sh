#!/usr/bin/env bash
# Detect WAL segment continuity gaps on a timeline.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/wal_name.sh"

continuity_gaps_json() {
  local archive="$1"
  python3 - "${archive}" <<'PY'
import json, sys
from pathlib import Path
archive = Path(sys.argv[1])
segments = []
for path in sorted(archive.iterdir()):
    if not path.is_file():
        continue
    name = path.name
    if name.endswith(".history") or name.endswith(".partial"):
        continue
    if len(name) == 24 and all(c in "0123456789abcdefABCDEF" for c in name):
        tl = int(name[0:8], 16)
        seg = int(name[8:24], 16)
        segments.append((tl, seg, name.upper()))
by = {}
for tl, seg, name in segments:
    by.setdefault(tl, []).append(seg)
gaps = []
for tl in sorted(by):
    nums = sorted(by[tl])
    for prev, cur in zip(nums, nums[1:]):
        if cur != prev + 1:
            gaps.append({
                "timeline": tl,
                "from_segment": f"{tl:08X}{prev:016X}",
                "to_segment": f"{tl:08X}{cur:016X}",
            })
print(json.dumps(gaps, separators=(",", ":")))
PY
}
