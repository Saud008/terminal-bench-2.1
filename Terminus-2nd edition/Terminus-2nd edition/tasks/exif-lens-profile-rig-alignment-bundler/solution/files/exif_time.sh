#!/usr/bin/env bash
normalize_exif_ms() {
  local raw="$1"
  local tz_min="$2"
  python3 - "$raw" "$tz_min" <<'PY'
import sys
from datetime import datetime, timezone

raw, tz_min = sys.argv[1], int(sys.argv[2])
dt = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
base_ms = int(dt.timestamp() * 1000)
print(base_ms - tz_min * 60000)
PY
}
