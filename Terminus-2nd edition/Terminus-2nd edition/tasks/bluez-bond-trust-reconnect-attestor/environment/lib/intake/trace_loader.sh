#!/usr/bin/env bash
set -euo pipefail

source /app/lib/common.sh

load_debounce_ms() {
  local cfg="$1"
  python3 - "$cfg" "${DEBOUNCE_MS_FILE}" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
open(sys.argv[2], "w", encoding="utf-8").write(str(int(doc["debounce_ms"])))
PY
}

sorted_trace_rows() {
  local trace="$1"
  python3 - "$trace" <<'PY'
import json, sys

rows = []
with open(sys.argv[1], encoding="utf-8") as fh:
    for raw in fh:
        line = raw.strip()
        if line:
            rows.append(json.loads(line))
rows.sort(key=lambda r: (int(r["seq"]), int(r.get("ts", 0))))
for row in rows:
    print(json.dumps(row))
PY
}
