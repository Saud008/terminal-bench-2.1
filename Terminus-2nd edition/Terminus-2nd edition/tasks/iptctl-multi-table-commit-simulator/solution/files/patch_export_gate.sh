#!/usr/bin/env bash

verify_staging_binding() {
  local staging="$1"
  python3 - "$staging" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

staging_path = Path(sys.argv[1])
if not staging_path.is_file():
    sys.exit(4)
staging = json.loads(staging_path.read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("ipt_engine", "/app/tools/simulate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
restore = Path(staging["restore_path"])
plan_digest = module.compute_plan_digest(restore, staging["phase_config"])
if staging.get("binding", {}).get("plan_digest") != plan_digest:
    sys.exit(4)
merge_path = module.merge_staging_path(staging_path)
if not merge_path.is_file():
    sys.exit(4)
merge = json.loads(merge_path.read_text(encoding="utf-8"))
expect = module.merge_staging_digest(staging)
if merge.get("merge_staging_digest") != expect:
    sys.exit(4)
if staging["binding"].get("merge_staging_digest") != expect:
    sys.exit(4)
sys.exit(0)
PY
  return $?
}
