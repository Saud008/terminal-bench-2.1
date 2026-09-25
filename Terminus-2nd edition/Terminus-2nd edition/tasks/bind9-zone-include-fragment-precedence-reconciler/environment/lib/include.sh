#!/usr/bin/env bash

# Include expansion and $INCLUDE walk helpers.
expand_zone_units() {
  local tree="$1"
  local master_rel="$2"
  local origin="$3"
  python3 - "$tree" "$master_rel" "$origin" <<'PY'
import json, subprocess, sys
from pathlib import Path

tree = Path(sys.argv[1])
master_rel = sys.argv[2]
origin = sys.argv[3]
visited = set()

def parse_file(abs_path: Path, rel: str, cur_origin: str):
    cmd = [
        "bash", "-c",
        'source /app/lib/common.sh; source /app/lib/parse.sh; parse_zone_file "$1" "$2"',
        "bash", str(abs_path), cur_origin,
    ]
    return json.loads(subprocess.check_output(cmd, text=True).strip())

def resolve(base: Path, rel_inc: str) -> Path:
    return (base.parent / rel_inc).resolve()

units = []
pending_includes = []

def walk(abs_path: Path, rel: str, cur_origin: str):
    if str(abs_path) in visited:
        return
    visited.add(str(abs_path))
    parsed = parse_file(abs_path, rel, cur_origin)
    cur_origin = parsed["records"][0]["origin"] if parsed["records"] else cur_origin
    for inc in parsed["includes"]:
        inc_abs = resolve(abs_path, inc["path"])
        inc_rel = str(inc_abs.relative_to(tree)) if inc_abs.is_relative_to(tree) else inc["path"]
        pending_includes.append((inc_abs, inc_rel, cur_origin))
    units.append({"file": rel, "records": parsed["records"]})

master_abs = tree / master_rel
walk(master_abs, master_rel, origin)
for inc_abs, inc_rel, cur_origin in pending_includes:
    if inc_abs.is_file():
        walk(inc_abs, inc_rel, cur_origin)

order = [u["file"] for u in units]
print(json.dumps({"processing_order": order, "units": units}))
PY
}
