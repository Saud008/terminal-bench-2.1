#!/usr/bin/env bash
# Parse basebackup backup_label files.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

parse_backup_label() {
  local archive="$1"
  local label="${archive}/backup_label"
  [[ -f "${label}" ]] || die "missing backup_label"
  python3 - "${label}" <<'PY'
import json, re, sys
from datetime import datetime, timezone
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
start_time = None
start_timeline = None
start_file = None
for line in text.splitlines():
    line = line.strip()
    if line.startswith("START TIME:"):
        raw = line.split(":", 1)[1].strip().replace(" UTC", "")
        start_time = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    elif line.startswith("START TIMELINE:"):
        start_timeline = int(line.split(":", 1)[1].strip(), 10)
    elif line.startswith("START WAL LOCATION:") and "file" in line:
        m = re.search(r"file\s+([0-9A-Fa-f]{24})", line)
        if m:
            start_file = m.group(1).upper()
if start_time is None or start_timeline is None or start_file is None:
    raise SystemExit("incomplete backup_label")
print(json.dumps({
    "start_time": start_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
    "start_timeline": start_timeline,
    "start_segment_file": start_file,
}, separators=(",", ":")))
PY
}
