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

def run_bash(fn, *args):
    env = {"PATH": "/usr/local/bin:/usr/bin:/bin"}
    if fn == "parse":
        cmd = [
            "bash",
            "-c",
            'source /app/lib/common.sh; source /app/lib/parse.sh; parse_fragment "$1"',
            "bash",
            *args,
        ]
    elif fn == "normalize":
        cmd = [
            "bash",
            "-c",
            'source /app/lib/common.sh; source /app/lib/normalize.sh; normalize_value "$1"',
            "bash",
            *args,
        ]
    else:
        raise ValueError(fn)
    return subprocess.check_output(cmd, env=env, text=True).strip()

parsed = json.loads(run_bash("parse", str(fragment)))
effective = dict(state["effective"])
sources = dict(state["sources"])
for ent in parsed["entries"]:
    value = run_bash("normalize", ent["value"])
    effective[ent["key"]] = value
    sources[ent["key"]] = {"file": rel, "line": ent["line"]}
print(json.dumps({"effective": effective, "sources": sources}))
PY
}
