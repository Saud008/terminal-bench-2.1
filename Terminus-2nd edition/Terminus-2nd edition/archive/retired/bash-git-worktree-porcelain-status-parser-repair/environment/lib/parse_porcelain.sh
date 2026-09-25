#!/usr/bin/env bash
# Parse porcelain=v2 -z streams into a JSON array of raw records.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

wt_parse_porcelain() {
  local input="$1"
  wt_require_file "${input}"
  python3 - "${input}" <<'PY'
import json
import re
import sys
from pathlib import Path

def ordinary_from_path(path: str) -> dict:
    return {
        "tag": "1",
        "xy": "MM",
        "sub": "N",
        "mH": "100644",
        "mI": "100644",
        "mW": "100644",
        "hH": ".",
        "hI": ".",
        "path": path,
    }

def parse_record(text: str) -> dict:
    tag = text[0]
    if tag == "1":
        parts = text.split(" ", 8)
        return {
            "tag": "1",
            "xy": parts[1],
            "sub": parts[2],
            "mH": parts[3],
            "mI": parts[4],
            "mW": parts[5],
            "hH": parts[6],
            "hI": parts[7],
            "path": parts[8],
        }
    if tag == "2":
        parts = text.split(" ", 8)
        tail = parts[8]
        m = re.match(r"^([RC])(\d+) (.+)$", tail)
        letter, score_s, paths = m.group(1), m.group(2), m.group(3)
        new_path, old_path = paths.split("\t", 1)
        return {
            "tag": "2",
            "xy": parts[1],
            "sub": parts[2],
            "mH": parts[3],
            "mI": parts[4],
            "mW": parts[5],
            "hH": parts[6],
            "hI": parts[7],
            "letter": letter,
            "score": int(score_s),
            "path": new_path,
            "old_path": old_path,
        }
    if tag == "u":
        parts = text.split(" ", 10)
        return {
            "tag": "u",
            "xy": parts[1],
            "sub": parts[2],
            "m1": parts[3],
            "m2": parts[4],
            "m3": parts[5],
            "mW": parts[6],
            "h1": parts[7],
            "h2": parts[8],
            "h3": parts[9],
            "path": parts[10],
        }
    if tag == "?":
        return {"tag": "?", "path": text[2:]}
    if tag == "!":
        return {"tag": "!", "path": text[2:]}
    raise ValueError(text)

text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="surrogateescape")
records = []
for line in text.splitlines():
    if not line:
        continue
    if line[0] == "2" and "\t" in line:
        left, right = line.split("\t", 1)
        records.append(ordinary_from_path(left.split()[-1]))
        records.append(ordinary_from_path(right))
        continue
    records.append(parse_record(line))
print(json.dumps(records, separators=(",", ":")))
PY
}
