#!/usr/bin/env bash
set -euo pipefail

parse_kconfig_file() {
  local path="$1"
  python3 - <<'PY' "$path"
import json, re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
symbols = {}
unset = re.compile(r'^#\s*(CONFIG_\w+)\s+is not set\s*$')
assign = re.compile(r'^(CONFIG_\w+)=(y|m|n)$')
for line in text.splitlines():
    line = line.strip()
    if not line or line.startswith("#") and "CONFIG_" not in line:
        continue
    m = unset.match(line)
    if m:
        symbols[m.group(1)] = "n"
        continue
    m = assign.match(line)
    if m:
        symbols[m.group(1)] = m.group(2)
print(json.dumps(symbols, sort_keys=True))
PY
}
