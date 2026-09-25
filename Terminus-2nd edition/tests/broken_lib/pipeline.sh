#!/usr/bin/env bash

run_prepare() {
  local scenario="$1"
  local seed="$2"
  local scenario_dir="$scenario"
  if [[ "$scenario" != /* ]]; then
    scenario_dir="/app/fixtures/scenarios/${scenario}"
  fi
  ingest_scenario "$scenario_dir"
  # Broken: skips epoch/staging/seal/custody init coupling
  init_ledger
  init_session_state
}

run_commit() {
  local out="$1"
  local scenario_label="unknown"
  local seed="alpha01"
  local requests="/app/fixtures/scenarios/001-single-spam/requests.json"
  python3 - "$requests" <<'PY' | while IFS= read -r row_json; do
import json, sys
req = json.load(open(sys.argv[1], encoding="utf-8"))
for row in req.get("releases", []):
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
      continue
    fi
    if attempt_release "$PARSED_QID" "$qclass"; then
      if [[ "${RELEASE_OK:-0}" -eq 1 ]]; then
        record_release_attempt "$PARSED_QID" "$qclass" "released" "$PARSED_QUEUE_ID"
        append_session_json '{"releases_succeeded": 1}'
      fi
    fi
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
