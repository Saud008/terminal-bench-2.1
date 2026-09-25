#!/usr/bin/env bash
# Parse quadlet trees into merged unit JSON.

set -euo pipefail

source /app/lib/common.sh

run_parse() {
  local tree="$1"
  local out="$2"
  ensure_output_dir
  python3 - "${tree}" "${TOUCH}" <<'PY' > "${out}"
import json, os, subprocess, sys
from pathlib import Path

tree = Path(sys.argv[1])
touch = Path(sys.argv[2])
parser = "/app/tools/quadlet_parser.py"

def file_meta(path: Path):
    proc = subprocess.run(
        [sys.executable, parser, "file-meta", "--file", str(path), "--touch", str(touch)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(proc.stdout)["sections"]

def unit_name(path: Path) -> str:
    return path.name[:-len(".container")] + ".service"

def dropins(base: Path):
    d = base.parent / f"{base.name}.d"
    if not d.is_dir():
        return []
    return [d / name for name in os.listdir(d) if name.endswith(".conf")]

def merge_lists(dst, src):
    for item in src:
        if item not in dst:
            dst.append(item)

units = {}
for base in sorted(tree.rglob("*.container")):
    name = unit_name(base)
    merged = {"unit": {}, "service": {}, "container": {}}
    fragments = [base] + dropins(base)
    for frag in fragments:
        sections = file_meta(frag)
        unit = sections.get("Unit", {})
        svc = sections.get("Service", {})
        ctr = sections.get("Container", {})
        for key in ("After", "Wants", "Requires"):
            if key in unit:
                merged["unit"].setdefault(key, [])
                merge_lists(merged["unit"][key], unit[key] if isinstance(unit[key], list) else [unit[key]])
        for key, val in unit.items():
            if key not in ("After", "Wants", "Requires"):
                merged["unit"][key] = val
        for key, val in svc.items():
            if key == "EnvironmentFile":
                merged["service"].setdefault(key, [])
                items = val if isinstance(val, list) else [val]
                merge_lists(merged["service"][key], items)
            else:
                merged["service"][key] = val
        for key, val in ctr.items():
            merged["container"][key] = val
    merged["source"] = str(base.resolve())
    units[name] = merged

print(json.dumps({"tree": str(tree.resolve()), "units": units}))
PY
}
