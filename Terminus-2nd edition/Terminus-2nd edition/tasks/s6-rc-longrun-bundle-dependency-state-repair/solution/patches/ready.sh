#!/usr/bin/env bash
# Longrun ready barrier (fixed).

set -euo pipefail

source /app/lib/common.sh
source /app/lib/ingest.sh

run_ready() {
  local tree="$1"
  local bundle="$2"
  local state_dir="$3"
  local out="$4"
  local tmp
  tmp="$(mktemp)"
  load_bundle "${tree}" "${bundle}" > "${tmp}"
  python3 - "${tmp}" "${state_dir}" > "${out}" <<'PY'
import json, sys
from pathlib import Path

bundle = json.loads(Path(sys.argv[1]).read_text())
state_dir = Path(sys.argv[2])
rc_path = state_dir / "services.json"
rc = {}
if rc_path.is_file():
    rc = json.loads(rc_path.read_text())

longruns = {}
hard_parents = {n: [] for n in bundle.get("longruns", [])}
for child, parent in bundle.get("hard_deps", []):
    if child in hard_parents:
        hard_parents[child].append(parent)
for name in sorted(bundle.get("longruns", [])):
    blocked = sorted({p for p in hard_parents.get(name, []) if rc.get(p, "down") != "up"})
    longruns[name] = {"ready": len(blocked) == 0, "blocked_by": blocked}

print(json.dumps({"bundle": bundle["name"], "longruns": longruns}, indent=2))
PY
  rm -f "${tmp}"
}
