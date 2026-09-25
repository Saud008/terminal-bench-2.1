#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/app"
STATE_DIR="${APP_ROOT}/state/run"
LEDGER_DIR="${APP_ROOT}/state/ledger/devices"
DEFAULT_MIDSTATE_PATH="${APP_ROOT}/state/bondattest-midstate.json"
DEFAULT_BUNDLE_PATH="${APP_ROOT}/output/bond-reconnect-attestation.json"
COUNTERS="${STATE_DIR}/counters.json"
LEDGER_LOG="${STATE_DIR}/ledger_rows.jsonl"
DISCONNECT_JSON="${STATE_DIR}/disconnect_reasons.json"
ADAPTER_POWER="${STATE_DIR}/adapter_power.txt"
GATT_SEEN="${STATE_DIR}/gatt_seen.txt"
LAST_RECONNECT_DIR="${STATE_DIR}/last_reconnect"
DEBOUNCE_MS_FILE="${STATE_DIR}/debounce_ms.txt"

ensure_runtime_dirs() {
  mkdir -p "${APP_ROOT}/state" "${APP_ROOT}/output"
}

init_run_state() {
  ensure_runtime_dirs
  rm -rf "${STATE_DIR}" "${LEDGER_DIR}"
  mkdir -p "${STATE_DIR}" "${LEDGER_DIR}" "${LAST_RECONNECT_DIR}"
  echo "on" > "${ADAPTER_POWER}"
  echo "500" > "${DEBOUNCE_MS_FILE}"
  echo '{"pairing_confirms":0,"resume_tokens_cleared":0,"gatt_resolve_count":0,"reconnect_attempts":0}' > "${COUNTERS}"
  : > "${LEDGER_LOG}"
  echo '[]' > "${DISCONNECT_JSON}"
  : > "${GATT_SEEN}"
}

sha256_hex() {
  python3 -c 'import hashlib, sys; print(hashlib.sha256(sys.argv[1].encode("utf-8")).hexdigest())' "$1"
}

bump_counter() {
  local key="$1"
  python3 - "$key" "${COUNTERS}" <<'PY'
import json, sys
path = sys.argv[2]
doc = json.load(open(path, encoding="utf-8"))
doc[sys.argv[1]] = int(doc.get(sys.argv[1], 0)) + 1
json.dump(doc, open(path, "w", encoding="utf-8"))
PY
}

append_ledger_row() {
  python3 - "$1" "${LEDGER_LOG}" <<'PY'
import json, sys
row = json.loads(sys.argv[1])
with open(sys.argv[2], "a", encoding="utf-8") as fh:
    fh.write(json.dumps(row, separators=(",", ":")) + "\n")
PY
}

read_adapter_power() {
  tr -d ' \n' < "${ADAPTER_POWER}"
}

write_adapter_power() {
  echo "$1" > "${ADAPTER_POWER}"
}

resolve_trace_path() {
  local trace="$1"
  if [[ "$trace" == /* ]]; then
    echo "$trace"
    return
  fi
  if [[ -n "${TB3_TRACE_DIR:-}" && "${TB3_TRACE_DIR}" == /* ]]; then
    echo "${TB3_TRACE_DIR}/${trace}"
    return
  fi
  echo "${APP_ROOT}/fixtures/traces/${trace}"
}
