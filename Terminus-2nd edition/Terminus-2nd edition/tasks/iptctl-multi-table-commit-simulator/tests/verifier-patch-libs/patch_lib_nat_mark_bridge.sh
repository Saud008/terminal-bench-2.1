#!/usr/bin/env bash

lib_phase_d_mark() {
  python3 - "${IPT_PARSED_PATH:-}" <<'PY'
import json
import sys
from pathlib import Path

parsed_path = sys.argv[1]
mode = "isolated"
if parsed_path and Path(parsed_path).is_file():
    tables = json.loads(Path(parsed_path).read_text(encoding="utf-8"))
    mangle_sets = any(
        "-j MARK" in rule.get("spec", "")
        for rule in tables.get("mangle", {}).get("rules", [])
    )
    nat_matches = any(
        "-m mark" in rule.get("spec", "")
        for rule in tables.get("nat", {}).get("rules", [])
    )
    if mangle_sets and nat_matches:
        mode = "linked"
print(mode)
PY
}
