#!/usr/bin/env bash

run_at_replay() {
  local scenario="$1"
  local seed="$2"
  local clock_epoch="$3"
  local out="$4"
  CLOCK_EPOCH="$clock_epoch"
  local scenario_dir="$scenario"
  if [[ "$scenario" != /* ]]; then
    scenario_dir="/app/fixtures/scenarios/${scenario}"
  fi
  local scenario_label="$scenario"
  if [[ "$scenario" == /* ]]; then
    scenario_label="$(basename "$scenario")"
  fi
  local conf="${scenario_dir}/scenario.conf.json"
  local timezone
  timezone="$(json_get "$conf" "system_timezone")"

  init_state
  copy_scenario_tree "$scenario_dir"

  local effective
  effective="$(effective_clock)"

  local jobs_json
  jobs_json="$(python3 - "$conf" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
rows = []
for batch in doc.get("batches", []):
    bid = batch["batch_id"]
    for job in batch.get("jobs", []):
        rows.append({"batch_id": bid, "job": job})
print(json.dumps(rows))
PY
)"

  local job_count
  job_count="$(python3 - "$jobs_json" <<'PY'
import json, sys
print(len(json.loads(sys.argv[1])))
PY
)"

  local idx=0
  while [[ "$idx" -lt "$job_count" ]]; do
    local row_json batch_id job_id atq_epoch script_rel exit_code start_letter umask_octal jkey
    row_json="$(python3 - "$jobs_json" "$idx" <<'PY'
import json, sys
rows = json.loads(sys.argv[1])
print(json.dumps(rows[int(sys.argv[2])]))
PY
)"
    batch_id="$(python3 - "$row_json" <<'PY'
import json, sys
row = json.loads(sys.argv[1])
print(row["batch_id"])
PY
)"
    job_id="$(python3 - "$row_json" <<'PY'
import json, sys
row = json.loads(sys.argv[1])
print(row["job"]["job_id"])
PY
)"
    atq_epoch="$(python3 - "$row_json" <<'PY'
import json, sys
row = json.loads(sys.argv[1])
print(row["job"]["atq_epoch"])
PY
)"
    script_rel="$(python3 - "$row_json" <<'PY'
import json, sys
row = json.loads(sys.argv[1])
print(row["job"]["script"])
PY
)"
    exit_code="$(python3 - "$row_json" <<'PY'
import json, sys
row = json.loads(sys.argv[1])
print(row["job"].get("exit_code", 0))
PY
)"
    start_letter="$(python3 - "$row_json" <<'PY'
import json, sys
row = json.loads(sys.argv[1])
print(row["job"].get("start_letter", "a"))
PY
)"
    umask_octal="$(python3 - "$row_json" <<'PY'
import json, sys
row = json.loads(sys.argv[1])
print(row["job"].get("umask", "0022"))
PY
)"
    jkey="$(job_key "$batch_id" "$job_id")"

    append_timeline "registry_read" "$jkey" "$effective"

    if [[ "$(schedule_is_due "$atq_epoch" "$effective")" != "true" ]]; then
      record_skip "$jkey" "not_due"
      idx=$((idx + 1))
      continue
    fi

    local seq_val letter spool_name
    seq_val="$(read_seq)"
    letter="$(allocate_letter "$start_letter" "$seq_val")"
    if [[ -z "$letter" ]]; then
      record_skip "$jkey" "no_slot"
      idx=$((idx + 1))
      continue
    fi
    append_timeline "slot_allocate" "$jkey" "$effective"
    record_slot_held "$letter"

    spool_name="$(write_spool_job "$letter" "$seq_val" "$batch_id" "$job_id" "$atq_epoch" "$script_rel")"
    append_timeline "spool_write" "$jkey" "$effective"

    bump_seq "$seq_val"
    append_timeline "seq_bump" "$jkey" "$effective"

    local meta_json
    meta_json="$(python3 - "$script_rel" "$umask_octal" <<'PY'
import json, sys
script_rel, umask = sys.argv[1:3]
interpreter = "sh"
path = f"/app/work/scripts/{script_rel}"
try:
    first = open(path, encoding="utf-8").readline().strip()
    if first.startswith("#!"):
        interpreter = first[2:].strip().split("/")[-1] or "sh"
except OSError:
    pass
print(json.dumps({"interpreter": interpreter, "effective_umask": format(int(umask, 8), "04o")}))
PY
)"
    registry_write_record "$batch_id" "$job_id" "$effective" "$meta_json"

    if notify_before_record_delete && [[ "$exit_code" -ne 0 ]]; then
      notify_failure "$jkey" "$exit_code" "$effective"
      append_timeline "mail_sent" "$jkey" "$effective"
    fi

    registry_delete_record "$batch_id" "$job_id" "$jkey" "$effective"

    if ! notify_before_record_delete && [[ "$exit_code" -ne 0 ]]; then
      notify_failure "$jkey" "$exit_code" "$effective"
      append_timeline "mail_sent" "$jkey" "$effective"
    fi

    local leave_pending
    leave_pending="$(python3 - "$conf" "$jkey" <<'PY'
import json, sys
doc = json.load(open(sys.argv[1], encoding="utf-8"))
jkey = sys.argv[2]
pending = doc.get("leave_pending", [])
print("true" if jkey in pending else "false")
PY
)"
    if [[ "$leave_pending" != "true" ]]; then
      complete_spool_job "$spool_name" "$letter"
      append_timeline "job_complete" "$jkey" "$effective"
      append_timeline "slot_release" "$jkey" "$effective"
    fi

    record_jobs_run "$jkey"
    idx=$((idx + 1))
  done

  append_timeline "atq_refresh" "system" "$effective"
  emit_export "$scenario_label" "$seed" "$effective" "$timezone" "$out"
}
