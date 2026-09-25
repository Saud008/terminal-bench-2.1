#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

write_drift_report() {
  local staging_path="$1"
  local out_path="$2"
  python3 - "${staging_path}" "${out_path}" <<'PY'
import json, sys
from pathlib import Path

stage = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out_path = Path(sys.argv[2])
evaluation = stage.get("evaluation") or {}
per_patch = evaluation.get("per_patch", [])
drift_count = sum(1 for row in per_patch if row.get("drift_flags"))
checksum_fail = sum(1 for row in per_patch if "PROFILE_CHECKSUM_MISMATCH" in row.get("drift_flags", []))
ticket_invalid = sum(1 for row in per_patch if "TICKET_EPOCH_INVALID" in row.get("drift_flags", []))
delta_drift = sum(1 for row in per_patch if "DRIFT_DELTA_E" in row.get("drift_flags", []))
report = {
    "schema": "icc-drift-report/1",
    "readings_digest": stage.get("readings_digest", ""),
    "profile_digest": stage.get("profile_digest", ""),
    "policy_digest": evaluation.get("policy_digest", ""),
    "profile_id": stage.get("profile_id", ""),
    "evaluated_as_of": evaluation.get("evaluated_as_of", 0),
    "summary": {
        "patch_count": len(per_patch),
        "drift_count": drift_count,
        "checksum_fail_count": checksum_fail,
        "ticket_invalid_count": ticket_invalid,
        "delta_e_drift_count": delta_drift,
    },
    "patches": per_patch,
}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(drift_count)
PY
}
