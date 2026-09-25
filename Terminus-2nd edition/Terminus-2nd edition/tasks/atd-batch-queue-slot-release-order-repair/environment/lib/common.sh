#!/usr/bin/env bash

WORK="/app/work"
SCRIPTS="${WORK}/scripts"
REGISTRY_DIR="${WORK}/registry"
SPOOL_DIR="/app/var/spool/at/jobs"
BATCH_SLOTS="/app/var/spool/at/batch_slots"
SEQ_FILE="/app/var/spool/at/.SEQ"
STATE="${WORK}/state.json"

json_get() {
  local file="$1"
  local key="$2"
  python3 - "$file" "$key" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
key = sys.argv[2]
cur = doc
for part in key.split("."):
    if isinstance(cur, dict):
        cur = cur.get(part)
    else:
        cur = None
        break
if cur is None:
    sys.exit(1)
if isinstance(cur, bool):
    print("true" if cur else "false")
else:
    print(cur)
PY
}

job_key() {
  echo "${1}:${2}"
}

script_path() {
  echo "${SCRIPTS}/${1}"
}

copy_scenario_tree() {
  local scenario_dir="$1"
  rm -rf "${SCRIPTS}" "${REGISTRY_DIR}"
  mkdir -p "${SCRIPTS}" "${REGISTRY_DIR}"
  if [[ -d "${scenario_dir}/scripts" ]]; then
    cp -a "${scenario_dir}/scripts/." "${SCRIPTS}/"
  fi
  if [[ -d "${scenario_dir}/registry" ]]; then
    cp -a "${scenario_dir}/registry/." "${REGISTRY_DIR}/"
  fi
  if [[ -d "${scenario_dir}/preexisting_spool" ]]; then
    cp -a "${scenario_dir}/preexisting_spool/." "${SPOOL_DIR}/"
  fi
  if [[ -f "${scenario_dir}/partial_seq" ]]; then
    cp "${scenario_dir}/partial_seq" "${SEQ_FILE}"
  fi
}

effective_clock() {
  if [[ -n "${TB3_CLOCK_EPOCH:-}" ]]; then
    echo "${TB3_CLOCK_EPOCH}"
  else
    echo "${CLOCK_EPOCH}"
  fi
}

init_spool_layout() {
  mkdir -p "${SPOOL_DIR}" "${BATCH_SLOTS}" "${WORK}" "${REGISTRY_DIR}"
  if [[ ! -f "${SEQ_FILE}" ]]; then
    echo "1" > "${SEQ_FILE}"
  fi
}

init_state() {
  init_spool_layout
  python3 - <<'PY'
import json
from pathlib import Path
state = {
    "timeline": [],
    "mail_log": [],
    "jobs_run": [],
    "jobs_skipped": [],
    "batch_slots_held": [],
}
Path("/app/work/state.json").write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

append_timeline() {
  local event="$1"
  local jkey="$2"
  local epoch="$3"
  python3 - "$STATE" "$event" "$jkey" "$epoch" <<'PY'
import json, sys
state_path, event, job, epoch = sys.argv[1:5]
state = json.load(open(state_path, encoding="utf-8"))
seq = len(state.get("timeline", [])) + 1
state.setdefault("timeline", []).append(
    {"seq": seq, "event": event, "job": job, "epoch": int(epoch)}
)
with open(state_path, "w", encoding="utf-8") as fh:
    json.dump(state, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

record_skip() {
  local jkey="$1"
  local reason="$2"
  python3 - "$STATE" "$jkey" "$reason" <<'PY'
import json, sys
state_path, job, reason = sys.argv[1:4]
state = json.load(open(state_path, encoding="utf-8"))
state.setdefault("jobs_skipped", []).append({"job": job, "reason": reason})
with open(state_path, "w", encoding="utf-8") as fh:
    json.dump(state, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

record_jobs_run() {
  local jkey="$1"
  python3 - "$STATE" "$jkey" <<'PY'
import json, sys
state_path, job = sys.argv[1:3]
state = json.load(open(state_path, encoding="utf-8"))
state.setdefault("jobs_run", []).append(job)
with open(state_path, "w", encoding="utf-8") as fh:
    json.dump(state, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

record_slot_held() {
  local letter="$1"
  python3 - "$STATE" "$letter" <<'PY'
import json, sys
state_path, letter = sys.argv[1:3]
state = json.load(open(state_path, encoding="utf-8"))
held = state.setdefault("batch_slots_held", [])
if letter not in held:
    held.append(letter)
with open(state_path, "w", encoding="utf-8") as fh:
    json.dump(state, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

record_slot_released() {
  local letter="$1"
  python3 - "$STATE" "$letter" <<'PY'
import json, sys
state_path, letter = sys.argv[1:3]
state = json.load(open(state_path, encoding="utf-8"))
held = [x for x in state.get("batch_slots_held", []) if x != letter]
state["batch_slots_held"] = held
with open(state_path, "w", encoding="utf-8") as fh:
    json.dump(state, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
}

schedule_is_due() {
  local atq_epoch="$1"
  local clock="$2"
  python3 - "$atq_epoch" "$clock" <<'PY'
import sys
print("true" if int(sys.argv[2]) >= int(sys.argv[1]) else "false")
PY
}
