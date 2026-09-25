#!/usr/bin/env bash

run_prepare() {
  local scenario="$1"
  local seed="$2"
  local scenario_dir="$scenario"
  if [[ "$scenario" != /* ]]; then
    scenario_dir="/app/fixtures/scenarios/${scenario}"
  fi
  local scenario_label="$scenario"
  if [[ "$scenario" == /* ]]; then
    scenario_label="$(basename "$scenario")"
  fi
  local requests="${scenario_dir}/requests.json"

  ingest_scenario "$scenario_dir"
  bump_release_epoch
  write_release_staging
  init_ledger
  init_session_state
  init_custody_journal
  write_prepare_seal "$scenario_label" "$seed" "$requests"
}

run_commit() {
  local out="$1"
  if ! read_prepare_seal; then
    echo "commit: missing prepare seal" >&2
    return 1
  fi
  local scenario_label="$SEAL_SCENARIO"
  local seed="$SEAL_SEED"
  local requests="$SEAL_REQUESTS"

  python3 - "$requests" "$seed" <<'PY' | while IFS= read -r row_json; do
import hashlib
import json
import re
import sys

requests_path, seed = sys.argv[1:3]
req = json.load(open(requests_path, encoding="utf-8"))
rows = list(req.get("releases", []))
qid_re = re.compile(r"Quarantine-ID:\s*([^\s,]+)")

def sort_key(row: dict) -> str:
    m = qid_re.search(row.get("log_line", ""))
    qid = m.group(1) if m else ""
    return hashlib.sha256(f"{seed}:{qid}".encode()).hexdigest()

if seed != "alpha01":
    rows = sorted(rows, key=sort_key)

for row in rows:
    print(json.dumps(row, separators=(",", ":")))
PY
    [[ -n "$row_json" ]] || continue
    local log_line qclass
    log_line="$(python3 - "$row_json" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["log_line"])
PY
)"
    qclass="$(python3 - "$row_json" <<'PY'
import json, sys
print(json.loads(sys.argv[1])["class"])
PY
)"
    append_session_json '{"releases_attempted": 1}'
    if ! extract_quarantine_id "$log_line"; then
      record_release_attempt "unknown" "$qclass" "failed" ""
      append_session_json '{"releases_failed": 1}'
      append_session_json "{\"release_log\": [{\"quarantine_id\": \"unknown\", \"class\": \"$qclass\", \"status\": \"failed\", \"sequence\": null}]}"
      continue
    fi
    if ! check_release_policy "$PARSED_QID" "$qclass" "$seed"; then
      record_release_attempt "$PARSED_QID" "$qclass" "failed" "$PARSED_QUEUE_ID"
      append_session_json '{"releases_failed": 1}'
      append_session_json "{\"release_log\": [{\"quarantine_id\": \"$PARSED_QID\", \"class\": \"$qclass\", \"status\": \"failed\", \"sequence\": null}]}"
      continue
    fi
    if attempt_release "$PARSED_QID" "$qclass"; then
      if [[ "${DUPLICATE_SKIPPED:-0}" -eq 1 ]]; then
        append_session_json '{"duplicate_skipped": 1}'
        append_session_json "{\"release_log\": [{\"quarantine_id\": \"$PARSED_QID\", \"class\": \"$qclass\", \"status\": \"duplicate_skipped\", \"sequence\": null}]}"
        continue
      fi
      if [[ "${RELEASE_OK:-0}" -eq 1 ]]; then
        record_release_attempt "$PARSED_QID" "$qclass" "released" "$PARSED_QUEUE_ID"
        local seq
        seq="$(ledger_tail_sequence)"
        append_custody_receipt "$PARSED_QID" "$qclass" "$seed" "$seq"
        append_session_json '{"releases_succeeded": 1}'
        append_session_json "{\"release_log\": [{\"quarantine_id\": \"$PARSED_QID\", \"class\": \"$qclass\", \"status\": \"released\", \"sequence\": $seq}]}"
        continue
      fi
    fi
    record_release_attempt "$PARSED_QID" "$qclass" "failed" "$PARSED_QUEUE_ID"
    append_session_json '{"releases_failed": 1}'
    append_session_json "{\"release_log\": [{\"quarantine_id\": \"$PARSED_QID\", \"class\": \"$qclass\", \"status\": \"failed\", \"sequence\": null}]}"
  done

  emit_export "$scenario_label" "$seed" "$out"
}

run_reconcile() {
  local scenario="$1"
  local seed="$2"
  local out="$3"
  run_prepare "$scenario" "$seed"
  run_commit "$out"
}
