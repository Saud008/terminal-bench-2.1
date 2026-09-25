#!/usr/bin/env bash

publish_export() {
  local snap="$1"
  local out="$2"
  verify_export_ready "$snap" || return $?
  local digest
  digest="$(canonical_snapshot_digest "$snap")"
  python3 - "$snap" "$out" "$digest" <<'PY'
import json, sys
from pathlib import Path

snap, out, digest = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
meta = json.loads(snap.read_text(encoding="utf-8"))
doc = {
    "apply_version": 1,
    "tree": meta["tree"],
    "seed": meta["seed"],
    "processing_order": meta["processing_order"],
    "effective": meta["effective"],
    "sources": meta["sources"],
    "stats": meta["stats"],
    "apply_digest": digest,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
}

export_apply() {
  local tree="$1"
  local seed="$2"
  local out="$3"
  local snap="${APP_ROOT:-/app}/state/.apply-snapshot.json"
  build_snapshot "$tree" "$seed" "$snap" || {
    local rc=$?
    if [[ "$rc" -eq 3 ]]; then
      return 0
    fi
    return "$rc"
  }
  publish_export "$snap" "$out"
}
