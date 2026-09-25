#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

read_stage_json() {
  local stage_file="$1"
  python3 - "${stage_file}" <<'PY'
import json, sys
from pathlib import Path
print(Path(sys.argv[1]).read_text(encoding="utf-8"))
PY
}

write_stage_json() {
  local stage_file="$1"
  local payload="$2"
  python3 - "${stage_file}" "${payload}" <<'PY'
import json, sys
from pathlib import Path
out, payload = sys.argv[1], json.loads(sys.argv[2])
Path(out).parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY
}
