#!/usr/bin/env bash

parse_fragment() {
  local path="$1"
  python3 - "$path" <<'PY'
import json, re, sys
from pathlib import Path

path = Path(sys.argv[1])
entries = []
errors = []
seen_keys = set()
for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
    line = raw.strip()
    if not line:
        continue
    if line.startswith("#"):
        continue
    line = line.split("#", 1)[0].strip()
    if not line:
        continue
    if "=" not in line:
        parts = line.split(None, 1)
        if len(parts) != 2:
            errors.append({"line": line_no, "reason": "malformed"})
            continue
        key, value = parts[0].strip(), parts[1].strip()
    else:
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
    if not key or "." not in key:
        errors.append({"line": line_no, "reason": "invalid_key", "key": key or None})
        continue
    if key in seen_keys:
        continue
    seen_keys.add(key)
    entries.append({"key": key, "value": value, "line": line_no})
print(json.dumps({"file": str(path), "entries": entries, "errors": errors}))
PY
}
