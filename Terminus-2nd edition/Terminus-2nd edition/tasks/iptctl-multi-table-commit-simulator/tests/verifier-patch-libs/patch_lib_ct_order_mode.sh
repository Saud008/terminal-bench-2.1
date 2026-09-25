#!/usr/bin/env bash

lib_phase_e_ct() {
  python3 - "${IPT_PARSED_PATH:-}" <<'PY'
import json
import sys
from pathlib import Path

parsed_path = sys.argv[1]
mode = "lexical"
if parsed_path and Path(parsed_path).is_file():
    tables = json.loads(Path(parsed_path).read_text(encoding="utf-8"))
    for table_name in ("filter", "mangle"):
        for rule in tables.get(table_name, {}).get("rules", []):
            spec = rule.get("spec", "")
            if "-m conntrack" in spec:
                if "-j CT" in spec and "--notrack" in spec:
                    continue
                mode = "chain"
                break
        if mode == "chain":
            break
print(mode)
PY
}
