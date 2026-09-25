#!/usr/bin/env bash
# Ingest bundle trees into JSON via bundle_parser.py.

set -euo pipefail

source /app/lib/common.sh

run_ingest() {
  local tree="$1"
  local out="$2"
  ensure_output_dir
  python3 /app/tools/bundle_parser.py ingest-tree --tree "${tree}" --touch "${TOUCH}" > "${out}"
}

load_bundle() {
  local tree="$1"
  local bundle="$2"
  local tmp
  tmp="$(mktemp)"
  run_ingest "${tree}" "${tmp}"
  python3 - "${tmp}" "${bundle}" <<'PY'
import json, sys
from pathlib import Path
data = json.loads(Path(sys.argv[1]).read_text())
name = sys.argv[2]
bundles = data["bundles"]
if name not in bundles:
    raise SystemExit(f"unknown bundle:{name}")
print(json.dumps(bundles[name]))
PY
  rm -f "${tmp}"
}
