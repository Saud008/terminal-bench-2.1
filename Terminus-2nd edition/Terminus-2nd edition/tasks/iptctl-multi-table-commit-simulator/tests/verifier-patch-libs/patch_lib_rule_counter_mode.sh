#!/usr/bin/env bash

lib_phase_c_rules() {
  python3 - "${IPT_PARSED_PATH:-}" <<'PY'
import json
import sys
from pathlib import Path

parsed_path = sys.argv[1]
mode = "strip"
if parsed_path and Path(parsed_path).is_file():
    tables = json.loads(Path(parsed_path).read_text(encoding="utf-8"))
    for block in tables.values():
        for rule in block.get("rules", []):
            if int(rule.get("packets", 0)) or int(rule.get("bytes", 0)):
                mode = "keep"
                break
        if mode == "keep":
            break
print(mode)
PY
}
