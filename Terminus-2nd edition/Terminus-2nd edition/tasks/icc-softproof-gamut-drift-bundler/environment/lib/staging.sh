#!/usr/bin/env bash
# BROKEN baseline: staging omits paper_digest and leaves evaluation stub.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/parse_readings.sh"

write_staging_snapshot() {
  local readings_path="$1"
  local profile_path="$2"
  local paper_path="$3"
  local staging_path="$4"
  require_file "${readings_path}"
  require_file "${profile_path}"
  local patches_json profile_id
  patches_json="$(parse_readings_json "${readings_path}")"
  profile_id="$(jq -r '.profile_id' "${profile_path}")"
  python3 - "${staging_path}" "${readings_path}" "${profile_path}" "${profile_id}" "${patches_json}" <<'PY'
import hashlib, json, sys
from pathlib import Path

staging_path = Path(sys.argv[1])
readings_path = Path(sys.argv[2])
profile_path = Path(sys.argv[3])
profile_id = sys.argv[4]
patches = json.loads(sys.argv[5])

def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

doc = {
    "schema": "icc-softproof-stage/1",
    "readings_digest": digest_file(readings_path),
    "profile_digest": digest_file(profile_path),
    "paper_digest": "",
    "profile_id": profile_id,
    "patches": patches,
    "evaluation": None,
}
staging_path.parent.mkdir(parents=True, exist_ok=True)
staging_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

evaluate_staging_snapshot() {
  local staging_path="$1"
  local profile_path="$2"
  local paper_path="$3"
  local policy_path="$4"
  local tickets_path="$5"
  local as_of="$6"
  python3 - "${staging_path}" "${as_of}" <<'PY'
import json, sys
from pathlib import Path

staging_path = Path(sys.argv[1])
as_of = int(sys.argv[2])
stage = json.loads(staging_path.read_text(encoding="utf-8"))
per_patch = []
for patch in stage.get("patches", []):
    per_patch.append(
        {
            "patch_id": patch["patch_id"],
            "delta_e": 0.0,
            "active_intent": "perceptual",
            "effective_gamma": None,
            "ticket_id": "",
            "drift_flags": [],
        }
    )
stage["evaluation"] = {
    "policy_digest": "",
    "evaluated_as_of": as_of,
    "profile_checksum_ok": True,
    "per_patch": per_patch,
}
staging_path.write_text(json.dumps(stage, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

update_run_registry() {
  local readings_path="$1"
  local registry_path="${2:-/app/state/run-registry.json}"
  python3 - "${readings_path}" "${registry_path}" <<'PY'
import hashlib, json, sys
from pathlib import Path

readings_path = Path(sys.argv[1])
registry_path = Path(sys.argv[2])
digest = hashlib.sha256(readings_path.read_bytes()).hexdigest()
doc = {"runs": []}
if registry_path.is_file():
    doc = json.loads(registry_path.read_text(encoding="utf-8"))
runs = doc.setdefault("runs", [])
runs.append({"readings_digest": digest, "count": 1})
registry_path.parent.mkdir(parents=True, exist_ok=True)
registry_path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
