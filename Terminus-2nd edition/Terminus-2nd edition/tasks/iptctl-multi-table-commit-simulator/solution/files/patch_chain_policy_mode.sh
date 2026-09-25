#!/usr/bin/env bash

lib_phase_b_policy() {
  python3 - "${IPT_PARSED_PATH:-}" <<'PY'
import json
import sys
from pathlib import Path

parsed_path = sys.argv[1]
mode = "strip"
if parsed_path and Path(parsed_path).is_file():
    tables = json.loads(Path(parsed_path).read_text(encoding="utf-8"))
    for block in tables.values():
        for pol in block.get("policies", []):
            if int(pol.get("packets", 0)) or int(pol.get("bytes", 0)):
                mode = "keep"
                break
        if mode == "keep":
            break
print(mode)
PY
}
