#!/usr/bin/env bash

write_spool_job() {
  local letter="$1"
  local seq_val="$2"
  local batch="$3"
  local job_id="$4"
  local atq_epoch="$5"
  local script_rel="$6"
  local name="${letter}$(printf '%010d' "$seq_val")"
  local path="${SPOOL_DIR}/${name}"
  python3 - "$path" "$atq_epoch" "$batch" "$job_id" "$(script_path "$script_rel")" <<'PY'
import json, sys
from pathlib import Path
path, atq_epoch, batch, job_id, script_path = sys.argv[1:6]
body = Path(script_path).read_text(encoding="utf-8") if Path(script_path).is_file() else "echo\n"
header = f"ATQ_EPOCH={atq_epoch} BATCH={batch} JOB={job_id}\n"
Path(path).parent.mkdir(parents=True, exist_ok=True)
Path(path).write_text(header + body, encoding="utf-8")
PY
  touch "${BATCH_SLOTS}/${letter}"
  echo "$name"
}

complete_spool_job() {
  local spool_name="$1"
  local letter="$2"
  rm -f "${SPOOL_DIR}/${spool_name}"
  release_batch_slot "$letter"
}

release_batch_slot() {
  local letter="$1"
  rm -f "${BATCH_SLOTS}/${letter}"
  record_slot_released "$letter"
}
