#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/cvls_paths.sh"

workspace=""
json_out=""
csv_out=""
while [ $# -gt 0 ]; do
  case "$1" in
    --workspace) workspace="$2"; shift 2 ;;
    --json) json_out="$2"; shift 2 ;;
    --csv) csv_out="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done

[ -n "${workspace}" ] && [ -n "${json_out}" ] && [ -n "${csv_out}" ] || exit 2

staging="$(workspace_staging_path "${workspace}")"
[ -f "${staging}" ] || exit 3

python3 - "${staging}" "${json_out}" "${csv_out}" <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")
from audit.compliance_engine import canonical_json, export_csv, export_report

staging_path = Path(sys.argv[1])
json_out = Path(sys.argv[2])
csv_out = Path(sys.argv[3])
staging = json.loads(staging_path.read_text(encoding="utf-8"))
if not staging.get("audit_complete"):
    raise SystemExit(3)

run_seq = 1
state_file = Path("/app/state/run-seq.json")
if state_file.is_file():
    state = json.loads(state_file.read_text(encoding="utf-8"))
    run_seq = int(state.get("run_seq", 1))

report = export_report(staging, run_seq=run_seq)
json_out.parent.mkdir(parents=True, exist_ok=True)
csv_out.parent.mkdir(parents=True, exist_ok=True)
json_out.write_text(canonical_json(report), encoding="utf-8")
csv_out.write_text(export_csv(report), encoding="utf-8")
PY

exit 0
