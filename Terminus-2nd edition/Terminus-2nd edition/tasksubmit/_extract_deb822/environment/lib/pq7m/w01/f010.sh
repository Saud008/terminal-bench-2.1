#!/usr/bin/env bash
# Parse deb822 .sources stanzas into JSON array.
set -euo pipefail

read_deb822_stanzas() {
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
        # Continuation lines are ignored in baseline reader.
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
