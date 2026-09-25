#!/usr/bin/env bash
# Validate EDL FCM header against bundle timecode map (stage preflight).
set -euo pipefail

validate_tc_map_header() {
  local edl="$1"
  local tc_map="$2"
  python3 - "${edl}" "${tc_map}" <<'PY'
import json, sys
from pathlib import Path
edl = Path(sys.argv[1]).read_text(encoding="utf-8").splitlines()
tc = json.load(open(sys.argv[2], encoding="utf-8"))
fcm = next((ln for ln in edl if ln.strip().startswith("FCM:")), "")
drop = "DROP FRAME" in fcm.upper()
if bool(tc.get("drop_frame")) != drop:
    raise SystemExit(11)
PY
}
