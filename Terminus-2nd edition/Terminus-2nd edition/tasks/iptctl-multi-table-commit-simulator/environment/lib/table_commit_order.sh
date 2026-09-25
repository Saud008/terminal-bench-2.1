#!/usr/bin/env bash

lib_phase_a_sequence() {
  python3 - "${IPT_PARSED_PATH:-}" <<'PY'
import json
import sys
from pathlib import Path

parsed_path = sys.argv[1]
if not parsed_path or not Path(parsed_path).is_file():
    for name in ("filter", "nat", "mangle"):
        print(name)
    raise SystemExit(0)

tables = json.loads(Path(parsed_path).read_text(encoding="utf-8"))
present = {name for name in tables.keys() if name in {"mangle", "nat", "filter"}}
mangle_sets = any(
    "-j MARK" in rule.get("spec", "")
    for rule in tables.get("mangle", {}).get("rules", [])
)
nat_matches = any(
    "-m mark" in rule.get("spec", "")
    for rule in tables.get("nat", {}).get("rules", [])
)
if mangle_sets and nat_matches:
    order = [name for name in ("nat", "mangle", "filter") if name in present]
else:
    order = [name for name in ("filter", "nat", "mangle") if name in present]
for name in order:
    print(name)
PY
}
