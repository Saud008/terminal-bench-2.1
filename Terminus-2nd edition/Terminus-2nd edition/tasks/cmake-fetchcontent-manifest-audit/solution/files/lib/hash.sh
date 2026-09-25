#!/usr/bin/env bash
# FetchContent tarball + pin audit (golden).

HASH_SNAPSHOT="/app/state/hash-audit-snapshot.json"

hash_audit_deps() {
  local tree_json="$1"
  local vendor_dir="$2"
  local pins_file="$3"
  local out="$4"

  python3 - <<'PY' "$tree_json" "$vendor_dir" "$pins_file" "$out" "$HASH_SNAPSHOT"
import hashlib
import json
import re
import sys
from pathlib import Path

tree_path, vendor_dir, pins_file, out_path, snap_path = sys.argv[1:6]
tree = json.loads(Path(tree_path).read_text(encoding="utf-8"))
pins_text = Path(pins_file).read_text(encoding="utf-8")
pin_map = {}
for m in re.finditer(
    r'set\s*\(\s*PIN_(.+?)_GIT_COMMIT\s+"([^"]+)"\s*\)',
    pins_text,
    flags=re.IGNORECASE,
):
    pin_map[m.group(1).lower()] = m.group(2)

deps_by_name = {}
for f in tree.get("files", []):
    for dep in f.get("fetchcontent", []):
        name = dep["name"]
        if name not in deps_by_name:
            deps_by_name[name] = dep

deps = []
failures = []
for name in sorted(deps_by_name):
    dep = deps_by_name[name]
    archive = dep.get("url", "")
    expected = (dep.get("url_hash") or "").lower()
    archive_path = Path(vendor_dir) / archive
    actual = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    pin_val = pin_map.get(name.lower(), "")
    ok = actual == expected and actual == pin_val
    if not ok:
        failures.append(name)
    deps.append(
        {
            "name": name,
            "archive": archive,
            "url_hash_expected": expected,
            "url_hash_actual": actual,
            "pin_field": "git_commit",
            "pin_value": pin_val,
            "ok": ok,
        }
    )

failures = sorted(failures)
snapshot = {
    "version": 1,
    "audited_names": [d["name"] for d in deps],
    "failures": failures,
}
snap = Path(snap_path)
snap.parent.mkdir(parents=True, exist_ok=True)
snap.write_text(json.dumps(snapshot, indent=2) + "\n", encoding="utf-8")

payload = {"deps": deps, "failures": failures}
outp = Path(out_path)
outp.parent.mkdir(parents=True, exist_ok=True)
outp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}
