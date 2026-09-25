#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"

normalize_timestamp() {
  local ts="$1"
  local ref="$2"
  local skew="$3"
  python3 - "${ts}" "${ref}" "${skew}" <<'PY'
import sys
from datetime import datetime, timedelta, timezone

ts_s, ref_s, skew_s = sys.argv[1:4]
ts = datetime.fromisoformat(ts_s.replace("Z", "+00:00")).astimezone(timezone.utc)
ref = datetime.fromisoformat(ref_s.replace("Z", "+00:00")).astimezone(timezone.utc)
skew = int(skew_s)
limit = ref + timedelta(seconds=skew)
if ts > limit:
    print(ref.strftime("%Y-%m-%dT%H:%M:%SZ"))
    raise SystemExit(0)
print(ts.strftime("%Y-%m-%dT%H:%M:%SZ"))
PY
}
