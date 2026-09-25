#!/usr/bin/env bash
# SEL blob header and record stride parsing.
set -euo pipefail

RECORD_STRIDE_ADJUST=0

sel_header_xor() {
  local file="$1"
  python3 - "${file}" <<'PY'
import sys
path = sys.argv[1]
data = open(path, "rb").read(8)
x = 0
for b in data[:7]:
    x ^= b
print(x & 0xFF)
PY
}

parse_sel_header() {
  local file="$1"
  local magic count rec_len stored_xor calc_xor
  magic="$(xxd -s 0 -l 4 -p "${file}")"
  [ "${magic}" = "53454c31" ] || return 1
  count="$(read_u16_le "${file}" 4)"
  rec_len="$(read_u8 "${file}" 6)"
  stored_xor="$(read_u8 "${file}" 7)"
  calc_xor="$(sel_header_xor "${file}")"
  [ "${stored_xor}" -eq "${calc_xor}" ] || return 1
  echo "${count} ${rec_len}"
}

record_stride() {
  local rec_len="$1"
  echo $((rec_len + RECORD_STRIDE_ADJUST))
}
