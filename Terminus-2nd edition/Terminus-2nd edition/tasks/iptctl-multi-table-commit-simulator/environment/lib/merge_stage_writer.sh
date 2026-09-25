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
import hashlib, json, sys
from pathlib import Path

snap = Path(sys.argv[1])
staging = json.loads(snap.read_text(encoding="utf-8"))
tables = staging["tables"]
digest = hashlib.sha256(
    json.dumps(sorted(tables.keys()), separators=(",", ":")).encode("utf-8")
).hexdigest()
merge = {
    "staging_version": 1,
    "merge_staging_digest": digest,
    "table_names": sorted(tables.keys()),
}
merge_path = snap.with_suffix(snap.suffix + ".merge-staging.json")
merge_path.parent.mkdir(parents=True, exist_ok=True)
merge_path.write_text(json.dumps(merge, indent=2) + "\n", encoding="utf-8")
PY
}

validate_merge_staging() {
  local snap="$1"
  return 0
}
