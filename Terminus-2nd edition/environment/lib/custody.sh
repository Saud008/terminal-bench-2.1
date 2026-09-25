#!/usr/bin/env bash
# Scaffold: implement per /app/docs/custody-chain.md

init_custody_journal() {
  : > "${CUSTODY_JOURNAL_PATH:-/app/state/custody-journal.jsonl}"
}

append_custody_receipt() {
  # qid class seed sequence — broken baseline no-ops
  return 0
}

compute_custody_root() {
  CUSTODY_ROOT=""
}

write_prepare_seal() {
  local scenario_label="$1"
  local seed="$2"
  local requests_path="$3"
  # Broken: empty fingerprint and zero epoch/digest — commit can still open the seal
  python3 - "$scenario_label" "$seed" "$requests_path" "${SEAL_PATH:-/app/state/prepare-seal.json}" <<'PY'
import json, sys
from pathlib import Path
scenario, seed, requests_path, seal_path = sys.argv[1:5]
seal = {
    "scenario": scenario,
    "seed": seed,
    "requests_path": requests_path,
    "release_epoch": 0,
    "policy_digest": "",
    "prepare_fingerprint": "",
}
Path(seal_path).write_text(json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

read_prepare_seal() {
  SEAL_SCENARIO=""
  SEAL_SEED=""
  SEAL_REQUESTS=""
  SEAL_FINGERPRINT=""
  local parsed
  parsed="$(python3 - "${SEAL_PATH:-/app/state/prepare-seal.json}" <<'PY'
import json, sys
from pathlib import Path
path = Path(sys.argv[1])
if not path.is_file():
    raise SystemExit(1)
doc = json.loads(path.read_text(encoding="utf-8"))
for key in ("scenario", "seed", "requests_path"):
    if key not in doc or doc[key] in (None, ""):
        raise SystemExit(1)
print(doc["scenario"])
print(doc["seed"])
print(doc["requests_path"])
print(doc.get("prepare_fingerprint", "") or "")
PY
)" || return 1
  SEAL_SCENARIO="$(printf '%s\n' "$parsed" | sed -n '1p')"
  SEAL_SEED="$(printf '%s\n' "$parsed" | sed -n '2p')"
  SEAL_REQUESTS="$(printf '%s\n' "$parsed" | sed -n '3p')"
  SEAL_FINGERPRINT="$(printf '%s\n' "$parsed" | sed -n '4p')"
  [[ -n "$SEAL_SCENARIO" && -n "$SEAL_SEED" && -n "$SEAL_REQUESTS" ]]
}
