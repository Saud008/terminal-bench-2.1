#!/usr/bin/env bash
# Restore target timestamp selection.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

select_restore_segment() {
  local archive="$1"
  local start_time="$2"
  local restore_target="$3"
  local config_root="${4:-/app/config}"
  python3 - "${archive}" "${start_time}" "${restore_target}" "${config_root}" <<'PY'
import json, sys
from datetime import datetime, timezone
from pathlib import Path

def parse_utc(text):
    return datetime.strptime(text.replace(" UTC", ""), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

archive = Path(sys.argv[1])
start_time = sys.argv[2]
restore_target = sys.argv[3]
config_root = Path(sys.argv[4])
clock = json.loads((config_root / "segment-clock.json").read_text(encoding="utf-8"))
seconds = int(clock["seconds_per_segment"])
base = parse_utc(start_time)
target = parse_utc(restore_target)
selected = None
best = None
for path in sorted(archive.iterdir()):
    if not path.is_file() or path.name.endswith(".history") or path.name.endswith(".partial"):
        continue
    name = path.name.upper()
    if len(name) != 24:
        continue
    seg = int(name[8:24], 16)
    end = base + seg * seconds
    if end <= target and (best is None or end > best):
        selected = name
        best = end
print(selected or "")
PY
}
