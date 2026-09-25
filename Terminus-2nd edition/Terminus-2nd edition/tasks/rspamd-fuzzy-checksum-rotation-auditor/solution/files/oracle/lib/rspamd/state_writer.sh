#!/usr/bin/env bash

RF_APP_ROOT="${RF_APP_ROOT:-/app}"
RF_RUN_PATH="${RF_RUN_PATH:-${RF_APP_ROOT}/state/rotation-run.json}"
RF_ROLLBACK_PATH="${RF_ROLLBACK_PATH:-${RF_APP_ROOT}/state/rotation-rollback.json}"

rf_write_rotation_run() {
  local key_epoch="$1"
  local checksum_algo_id="$2"
  local mails_processed="$3"
  local unique_shingles="$4"
  local total_rows="$5"
  local console_matched="$6"
  python3 - "$key_epoch" "$checksum_algo_id" "$mails_processed" \
    "$unique_shingles" "$total_rows" "$console_matched" "$RF_RUN_PATH" <<'PY'
import json
import sys
import time
from pathlib import Path

ke, algo, mails, uniq, rows, console, out = sys.argv[1:8]
doc = {
    "schema": 1,
    "key_epoch": int(ke),
    "checksum_algo_id": int(algo),
    "mails_processed": int(mails),
    "unique_shingles": int(uniq),
    "total_shingle_rows": int(rows),
    "console_lines_matched": int(console),
    "completed_at": int(time.time()),
}
Path(out).parent.mkdir(parents=True, exist_ok=True)
Path(out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}

rf_write_rollback() {
  local key_epoch="$1"
  local checksum_algo_id="$2"
  local reason="$3"
  python3 - "$key_epoch" "$checksum_algo_id" "$reason" "$RF_ROLLBACK_PATH" <<'PY'
import json
import sys
from pathlib import Path

ke, algo, reason, out = sys.argv[1:5]
doc = {
    "schema": 1,
    "key_epoch": int(ke),
    "checksum_algo_id": int(algo),
    "reason": reason,
}
Path(out).parent.mkdir(parents=True, exist_ok=True)
Path(out).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
}
