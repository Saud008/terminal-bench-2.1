#!/usr/bin/env bash
# Parse quadlet trees into merged unit JSON (fixed).

set -euo pipefail

source /app/lib/common.sh

run_parse() {
  local tree="$1"
  local out="$2"
  ensure_output_dir
  python3 - "${tree}" "${TOUCH}" <<'PY' > "${out}"
import json, subprocess, sys
from pathlib import Path

sys.path.insert(0, "/app/tools")
from quadlet_parser import file_meta, list_dropins, unit_name_from_container

tree = Path(sys.argv[1])
touch = Path(sys.argv[2])
parser = "/app/tools/quadlet_parser.py"

def load_sections(path: Path):
    proc = __import__("subprocess").run(
        [sys.executable, parser, "file-meta", "--file", str(path), "--touch", str(touch)],
        capture_output=True, text=True, check=True,
    )
    return json.loads(proc.stdout)["sections"]

def merge_lists(dst, src):
    for item in src:
        if item not in dst:
            dst.append(item)

units = {}
for base in sorted(tree.rglob("*.container")):
    name = unit_name_from_container(base)
    merged = {"unit": {}, "service": {}, "container": {}}
    fragments = [base] + list_dropins(base)
    # phase 1: Wants/Requires/EnvironmentFile and scalars
    for frag in fragments:
        sections = load_sections(frag)
        unit = sections.get("Unit", {})
        svc = sections.get("Service", {})
        ctr = sections.get("Container", {})
        for key in ("Wants", "Requires"):
            if key in unit:
                merged["unit"].setdefault(key, [])
                vals = unit[key] if isinstance(unit[key], list) else [unit[key]]
                merge_lists(merged["unit"][key], vals)
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
    # phase 2: After= from all fragments
    for frag in fragments:
        sections = load_sections(frag)
        unit = sections.get("Unit", {})
        if "After" in unit:
            merged["unit"].setdefault("After", [])
            vals = unit["After"] if isinstance(unit["After"], list) else [unit["After"]]
            merge_lists(merged["unit"]["After"], vals)
    merged["source"] = str(base.resolve())
    units[name] = merged

print(json.dumps({"tree": str(tree.resolve()), "units": units}))
PY
}
