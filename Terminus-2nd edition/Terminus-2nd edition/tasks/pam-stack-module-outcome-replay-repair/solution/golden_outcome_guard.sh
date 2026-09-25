#!/usr/bin/env bash
# Outcome snapshot validation before export.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pamreplay_validate_outcome_snapshot() {
  local outcome_path="$1"
  python3 - "$outcome_path" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit("outcome snapshot missing")
snap = json.loads(path.read_text(encoding="utf-8"))
allowed = {"version", "stack", "user", "exit_code", "phases", "environment", "audit_path"}
extra = set(snap) - allowed
if extra:
    raise SystemExit(f"outcome snapshot has unexpected keys: {sorted(extra)}")
if snap.get("version") != 1:
    raise SystemExit("outcome snapshot version must be 1")
phases = snap.get("phases", [])
rank = {"auth": 0, "account": 1, "password": 2, "session": 3}
ranks = [rank[p["phase"]] for p in phases]
if ranks != sorted(ranks):
    raise SystemExit("outcome phases must follow execution order")
failed = any(p.get("status") == "fail" for p in phases)
exit_code = int(snap.get("exit_code", 0))
if failed and exit_code == 0:
    raise SystemExit("outcome exit_code must be non-zero when a phase failed")
if not failed and exit_code != 0:
    raise SystemExit("outcome exit_code must be zero when all phases succeeded")
PY
}
