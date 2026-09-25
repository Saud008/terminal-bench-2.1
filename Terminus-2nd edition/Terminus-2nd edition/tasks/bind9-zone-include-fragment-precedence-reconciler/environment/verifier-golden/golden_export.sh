#!/usr/bin/env bash

publish_export() {
  local snap="$1"
  local out="$2"
  local digest
  digest="$(canonical_snapshot_digest "$snap")"
  python3 - "$snap" "$out" "$digest" <<'PY'
import json, sys
from pathlib import Path

snap, out, digest = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
meta = json.loads(snap.read_text(encoding="utf-8"))
doc = {
    "compile_version": 1,
    "tree": meta["tree"],
    "seed": meta["seed"],
    "origin": meta["origin"],
    "processing_order": meta["processing_order"],
    "records": meta["records"],
    "soa_serial": meta["soa_serial"],
    "wildcard_conflicts": meta["wildcard_conflicts"],
    "nsec_valid": meta["nsec_valid"],
    "include_fingerprint": meta["include_fingerprint"],
    "zone_hash": meta.get("zone_hash"),
    "compile_digest": digest,
    "stats": meta["stats"],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
PY
}

export_compile() {
  local tree="$1"
  local seed="$2"
  local out="$3"
  local reload="${4:-0}"
  local snap="${APP_ROOT:-/app}/state/.compile-snapshot.json"
  build_snapshot "$tree" "$seed" "$snap" "$reload"
  publish_export "$snap" "$out"
}

cmd_verify_snapshot() {
  local snap="$1"
  python3 - "$snap" <<'PY'
import json, sys
from pathlib import Path

meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
issues = []
if meta.get("wildcard_conflicts"):
    issues.append("wildcard")
if not meta.get("nsec_valid", True):
    issues.append("nsec")
print(json.dumps({"ok": len(issues) == 0, "issues": issues}))
PY
}
