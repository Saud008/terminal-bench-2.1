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

def parse_record(text: str) -> dict:
    if not text:
        raise ValueError("empty record")
    tag = text[0]
    if tag == "1":
        parts = text.split(" ", 8)
        if len(parts) < 9:
            raise ValueError(f"short ordinary record: {text!r}")
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
        if len(parts) < 9:
            raise ValueError(f"short rename record: {text!r}")
        tail = parts[8]
        m = re.match(r"^([RC])(\d+) (.+)$", tail)
        if not m:
            raise ValueError(f"bad rename tail: {tail!r}")
        letter, score_s, paths = m.group(1), m.group(2), m.group(3)
        if "\t" not in paths:
            raise ValueError(f"missing tab in rename paths: {paths!r}")
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
        if len(parts) < 11:
            raise ValueError(f"short unmerged record: {text!r}")
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
    raise ValueError(f"unknown tag: {tag!r}")

raw = Path(sys.argv[1]).read_bytes()
records = []
for chunk in raw.split(b"\0"):
    if not chunk:
        continue
    records.append(parse_record(chunk.decode("utf-8")))
print(json.dumps(records, separators=(",", ":")))
PY
}
