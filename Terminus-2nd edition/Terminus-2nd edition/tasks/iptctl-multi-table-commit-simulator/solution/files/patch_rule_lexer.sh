#!/usr/bin/env bash

restore_exists() {
  [[ -f "$1" ]]
}

parse_restore_file() {
  local restore="$1"
  local out="$2"
  python3 - "$restore" "$out" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

restore = Path(sys.argv[1])
out = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("ipt_engine", "/app/tools/simulate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
tables = module.parse_restore(restore)
out.write_text(json.dumps(tables, indent=2) + "\n", encoding="utf-8")
PY
}
