#!/usr/bin/env bash
set -euo pipefail

deb822_to_json() {
  local path="$1"
  python3 - <<'PY' "$path"
import json, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
stanzas, cur, last_key = [], {}, None
for line in text.splitlines():
    if not line.strip():
        if cur:
            stanzas.append(cur)
            cur, last_key = {}, None
        continue
    if line.startswith(" "):
        if last_key:
            cur[last_key] = (cur.get(last_key, "") + " " + line.strip()).strip()
        continue
    if ":" in line:
        k, v = line.split(":", 1)
        last_key = k.strip()
        cur[last_key] = v.strip()
if cur:
    stanzas.append(cur)
print(json.dumps(stanzas))
PY
}
