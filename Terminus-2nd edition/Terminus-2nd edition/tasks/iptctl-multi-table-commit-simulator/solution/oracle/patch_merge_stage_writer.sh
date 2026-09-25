#!/usr/bin/env bash

staging_merge_path_for() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import sys
from pathlib import Path

snap = Path(sys.argv[1])
print(str(snap.with_suffix(snap.suffix + ".merge-staging.json")))
PY
}

write_merge_staging() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

snap = Path(sys.argv[1])
staging = json.loads(snap.read_text(encoding="utf-8"))
spec = importlib.util.spec_from_file_location("ipt_engine", "/app/tools/simulate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
digest = module.merge_staging_digest(staging)
merge = {
    "staging_version": 1,
    "merge_staging_digest": digest,
    "table_names": sorted(staging["tables"].keys()),
}
merge_path = module.merge_staging_path(snap)
merge_path.parent.mkdir(parents=True, exist_ok=True)
merge_path.write_text(json.dumps(merge, indent=2) + "\n", encoding="utf-8")
staging["binding"]["merge_staging_digest"] = digest
snap.write_text(json.dumps(staging, indent=2) + "\n", encoding="utf-8")
PY
}

validate_merge_staging() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import importlib.util
import json
import sys
from pathlib import Path

snap = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("ipt_engine", "/app/tools/simulate.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
merge_path = module.merge_staging_path(snap)
if not merge_path.is_file():
    sys.exit(4)
staging = json.loads(snap.read_text(encoding="utf-8"))
merge = json.loads(merge_path.read_text(encoding="utf-8"))
expect = module.merge_staging_digest(staging)
if merge.get("merge_staging_digest") != expect:
    sys.exit(4)
if staging["binding"].get("merge_staging_digest") != expect:
    sys.exit(4)
sys.exit(0)
PY
}
