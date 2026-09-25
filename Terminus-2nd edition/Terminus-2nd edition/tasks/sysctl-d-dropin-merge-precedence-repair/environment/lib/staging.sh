#!/usr/bin/env bash

source "${APP_ROOT:-/app}/lib/bind.sh"

staging_path_for() {
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
  local digest
  digest="$(legacy_staging_digest "$snap")"
  python3 - "$snap" "$digest" <<'PY'
import json, sys
from pathlib import Path

snap = Path(sys.argv[1])
digest = sys.argv[2]
meta = json.loads(snap.read_text(encoding="utf-8"))
layer_keys = []
for rel in meta["processing_order"]:
    layer_keys.append({"file": rel, "keys": sorted(meta["effective"].keys())})
staging = {
    "staging_version": 1,
    "snapshot_digest": digest,
    "layer_keys": layer_keys,
    "last_file": meta["processing_order"][-1] if meta["processing_order"] else "",
}
staging_path = snap.with_suffix(snap.suffix + ".merge-staging.json")
staging_path.parent.mkdir(parents=True, exist_ok=True)
staging_path.write_text(json.dumps(staging, indent=2) + "\n", encoding="utf-8")
PY
}

validate_merge_staging() {
  return 0
}

# Legacy helper — not used by ingest/export. Authoritative order is drop_in_order.
lexicographic_order() {
  local tree="$1"
  python3 - "$tree" <<'PY'
import json, sys
from pathlib import Path

tree = Path(sys.argv[1])
manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
drop_ins = sorted(manifest.get("drop_ins", []))
print("\n".join(drop_ins))
PY
}
