#!/usr/bin/env bash
# BROKEN baseline: no parent walk for gamma_anchor inheritance.
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
row = idx.get(batch_id)
if not row or row.get("gamma_anchor") is None:
    print("null")
else:
    print(float(row["gamma_anchor"]))
PY
}
