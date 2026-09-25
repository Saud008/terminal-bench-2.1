#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "${BASH_SOURCE[0]}")/../common.sh"

parse_pam_lines() {
  local file="$1"
  python3 - "$file" <<'PY'
import json, sys
from pathlib import Path
rows = []
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    if line.startswith("@"):
        rows.append({"kind": "directive", "text": line})
        continue
    parts = line.split()
    if len(parts) < 3:
        continue
    rows.append({
        "kind": "module",
        "type": parts[0],
        "control": parts[1],
        "module": parts[2],
        "args": parts[3:],
    })
print(json.dumps(rows))
PY
}
