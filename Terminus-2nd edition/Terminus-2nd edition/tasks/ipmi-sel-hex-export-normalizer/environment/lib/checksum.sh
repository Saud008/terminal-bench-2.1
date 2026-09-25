#!/usr/bin/env bash
# Per-record XOR checksum helpers.
set -euo pipefail

record_body_xor() {
  local file="$1"
  local offset="$2"
  local length="$3"
  python3 - "${file}" "${offset}" "${length}" <<'PY'
import sys
path, off, ln = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
data = open(path, "rb").read()[off:off+ln]
x = 0
for b in data:
    x ^= b
print(x & 0xFF)
PY
}

verify_record_checksum() {
  local file="$1"
  local offset="$2"
  local rec_len="$3"
  local body_len=$((rec_len - 1))
  local calc stored
  calc="$(record_body_xor "${file}" "${offset}" "${body_len}")"
  stored="$(read_u8 "${file}" $((offset + body_len)))"
  [ "${calc}" -eq "${stored}" ]
}

parse_record_fields() {
  local file="$1"
  local offset="$2"
  local rid rtype ts gen rev stype snum edir etype sev
  rid="$(read_u16_le "${file}" "${offset}")"
  rtype="$(read_u8 "${file}" $((offset + 2)))"
  ts="$(read_u32_le "${file}" $((offset + 3)))"
  gen="$(read_u16_le "${file}" $((offset + 7)))"
  rev="$(read_u8 "${file}" $((offset + 9)))"
  stype="$(read_u8 "${file}" $((offset + 10)))"
  snum="$(read_u8 "${file}" $((offset + 11)))"
  edir="$(read_u8 "${file}" $((offset + 12)))"
  etype=$((edir & 0x0F))
  sev="$(severity_for_event_type "${etype}")"
  echo "${rid} ${rtype} ${ts} ${gen} ${rev} ${stype} ${snum} ${etype} ${sev}"
}
