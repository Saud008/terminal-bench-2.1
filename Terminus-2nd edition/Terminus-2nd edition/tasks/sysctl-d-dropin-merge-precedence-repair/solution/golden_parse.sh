#!/usr/bin/env bash

parse_fragment() {
  local path="$1"
  python3 - "$path" <<'PY'
import json, re, sys
from pathlib import Path

KEY_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")

def strip_inline_comment(line: str) -> str:
    for idx, ch in enumerate(line):
        if ch == "#" and idx > 0 and line[idx - 1].isspace():
            return line[:idx].rstrip()
    return line.strip()

def parse_assignment(line: str):
    m = re.match(r"^([a-z0-9][a-z0-9_.-]*)\s*=\s*(.+)$", line, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2).strip()
    m = re.match(r"^([a-z0-9][a-z0-9_.-]*)\s+(\S.*)$", line, re.IGNORECASE)
    if m:
        return m.group(1), m.group(2).strip()
    return None

path = Path(sys.argv[1])
entries = []
errors = []
for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    line = strip_inline_comment(line)
    if not line:
        continue
    parsed = parse_assignment(line)
    if not parsed:
        errors.append({"line": line_no, "reason": "malformed"})
        continue
    key, value = parsed
    if "." not in key or not KEY_RE.match(key):
        errors.append({"line": line_no, "reason": "invalid_key", "key": key})
        continue
    entries.append({"key": key, "value": value, "line": line_no})
print(json.dumps({"file": str(path), "entries": entries, "errors": errors}))
PY
}
