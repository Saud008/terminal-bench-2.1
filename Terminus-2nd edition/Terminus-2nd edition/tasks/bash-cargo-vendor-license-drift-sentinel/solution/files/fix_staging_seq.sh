#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/cvls_paths.sh"

workspace="$1"
staging="$2"

STATE_DIR="${APP_ROOT}/state"
mkdir -p "${STATE_DIR}"

python3 - "${workspace}" "${staging}" "${STATE_DIR}/run-seq.json" <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")
from audit.compliance_engine import workspace_fingerprint

ws = Path(sys.argv[1])
staging_path = Path(sys.argv[2])
state_path = Path(sys.argv[3])

staging = json.loads(staging_path.read_text(encoding="utf-8"))
fp = staging.get("workspace_fingerprint") or workspace_fingerprint(ws)

run_seq = 1
if state_path.is_file():
    state = json.loads(state_path.read_text(encoding="utf-8"))
    run_seq = int(state.get("run_seq", 0))
    if state.get("last_workspace_fingerprint") != fp:
        run_seq += 1
else:
    run_seq = 1

state_path.write_text(
    json.dumps(
        {
            "run_seq": run_seq,
            "last_workspace_fingerprint": fp,
            "workspace_id": staging.get("workspace_id", ws.name),
        },
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
PY

echo "${workspace}" > "${STATE_DIR}/active-workspace.path"
exit 0
