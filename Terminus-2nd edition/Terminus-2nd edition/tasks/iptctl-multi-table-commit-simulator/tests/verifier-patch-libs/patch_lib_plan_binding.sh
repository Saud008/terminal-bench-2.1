#!/usr/bin/env bash

lib_plan_digest() {
  local restore="$1"
  python3 - "$restore" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

restore = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("ipt_engine", "/app/tools/simulate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cfg = module.load_runtime_config()
phase = module.phase_config_from_runtime(cfg)
print(module.compute_plan_digest(restore, phase))
PY
}
