#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

effective_gamma() {
  local batch_id="$1"
  local paper_path="$2"
  python3 - "${batch_id}" "${paper_path}" <<'PY'
import json, sys
from pathlib import Path

batch_id = sys.argv[1]
paper = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
idx = {b["id"]: b for b in paper.get("batches", [])}
current = batch_id
visited = set()
while current:
    if current in visited:
        print("null")
        raise SystemExit(0)
    visited.add(current)
    row = idx.get(current)
    if not row:
        print("null")
        raise SystemExit(0)
    anchor = row.get("gamma_anchor")
    if anchor is not None:
        print(float(anchor))
        raise SystemExit(0)
    parent = row.get("parent")
    current = str(parent) if parent else ""
print("null")
PY
}
