#!/usr/bin/env bash
# BROKEN baseline: export rebuilds from raw readings path not staging evaluation.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/parse_readings.sh"

write_drift_report() {
  local staging_path="$1"
  local out_path="$2"
  local readings_hint="${3:-}"
  python3 - "${staging_path}" "${out_path}" "${readings_hint}" <<'PY'
import json, sys
from pathlib import Path

stage = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out_path = Path(sys.argv[2])
patches = stage.get("patches", [])
per_patch = []
for patch in patches:
    per_patch.append(
        {
            "patch_id": patch["patch_id"],
            "delta_e": 0.0,
            "active_intent": "",
            "effective_gamma": None,
            "ticket_id": "",
            "drift_flags": [],
        }
    )
report = {
    "schema": "icc-drift-report/1",
    "readings_digest": stage.get("readings_digest", ""),
    "profile_digest": stage.get("profile_digest", ""),
    "policy_digest": "",
    "profile_id": stage.get("profile_id", ""),
    "evaluated_as_of": 0,
    "summary": {
        "patch_count": len(per_patch),
        "drift_count": 0,
        "checksum_fail_count": 0,
        "ticket_invalid_count": 0,
        "delta_e_drift_count": 0,
    },
    "patches": per_patch,
}
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(0)
PY
}
