#!/usr/bin/env bash

merge_fragment_into_state() {
  local fragment="$1"
  local rel="$2"
  local state_json="$3"
  python3 - "$fragment" "$rel" "$state_json" <<'PY'
import json, subprocess, sys
from pathlib import Path

fragment = Path(sys.argv[1])
rel = sys.argv[2]
state = json.loads(sys.argv[3])

def parse_fragment(path: Path) -> dict:
    cmd = [
        "bash",
        "-c",
        'source /app/lib/common.sh; source /app/lib/parse.sh; parse_fragment "$1"',
        "bash",
        str(path),
    ]
    return json.loads(subprocess.check_output(cmd, text=True).strip())

parsed = parse_fragment(fragment)
effective = {}
sources = {}
for ent in parsed["entries"]:
    effective[ent["key"]] = ent["value"]
    sources[ent["key"]] = {"file": rel, "line": ent["line"]}
print(json.dumps({"effective": effective, "sources": sources}))
PY
}
