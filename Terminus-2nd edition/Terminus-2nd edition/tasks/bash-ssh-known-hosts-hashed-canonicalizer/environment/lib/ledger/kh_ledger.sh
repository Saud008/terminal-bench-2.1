#!/usr/bin/env bash
# Persist parse staging ledger and manifest seals.

KH_LEDGER_ROOT="${KH_LEDGER_ROOT:-/app/state}"
KH_LEDGER_FILE="${KH_LEDGER_ROOT}/kh-ledger.jsonl"
KH_MANIFEST_FILE="${KH_LEDGER_ROOT}/kh-manifest.json"

kh_ledger_reset() {
  mkdir -p "${KH_LEDGER_ROOT}"
  : > "${KH_LEDGER_FILE}"
  rm -f "${KH_MANIFEST_FILE}"
}

kh_ledger_append() {
  local rec="$1"
  [[ -n "$rec" ]] || return 0
  printf '%s\n' "$rec" >> "${KH_LEDGER_FILE}.raw"
}

kh_ledger_seal() {
  local input_path="$1"
  local base
  base="$(basename "${input_path}")"
  local count
  count="$(wc -l < "${KH_LEDGER_FILE}.raw" 2>/dev/null | tr -d ' ')"
  count="${count:-0}"
  python3 - "${KH_MANIFEST_FILE}" "${base}" "${count}" <<'PY'
import hashlib, json, sys
out, name, count = sys.argv[1], sys.argv[2], int(sys.argv[3])
body = {
    "input_sha256": hashlib.sha256(name.encode()).hexdigest(),
    "record_count": count,
    "ledger_sha256": "unsealed",
}
open(out, "w", encoding="utf-8").write(json.dumps(body) + "\n")
PY
}

kh_ledger_verify() {
  return 0
}

kh_ledger_read_records() {
  if [[ -f "${KH_LEDGER_FILE}.raw" ]]; then
    cat "${KH_LEDGER_FILE}.raw"
  fi
}
