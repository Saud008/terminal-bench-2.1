#!/usr/bin/env bash
# Segment CRC32 rolling checksum (see /app/docs/wal-format.md).
set -euo pipefail

wal_crc32_range() {
  local file="$1"
  local offset="$2"
  local length="$3"
  local seed="$4"
  python3 - "${file}" "${offset}" "${length}" "${seed}" <<'PY'
import sys, zlib
path, off, ln, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
data = open(path, "rb").read()[off:off+ln]
print(zlib.crc32(data, seed) & 0xFFFFFFFF)
PY
}

verify_frame_checksum() {
  local wal="$1"
  local frame_idx="$2"
  local psz="$3"
  local salt1="$4"
  local salt2="$5"
  local base=$((32 + (frame_idx - 1) * (24 + psz)))
  local stored0 stored1 c0 c1 xor
  stored0="$(read_u32_be "${wal}" $((base + 16)))"
  stored1="$(read_u32_be "${wal}" $((base + 20)))"
  c0="$(wal_crc32_range "${wal}" "${base}" 8 "${salt1}")"
  xor=$(( (salt2 ^ c0) & 0xFFFFFFFF ))
  c1="$(wal_crc32_range "${wal}" $((base + 8)) 8 "${xor}")"
  c0="$(wal_crc32_range "${wal}" $((base + 24)) "${psz}" "${c1}")"
  c1="$(wal_crc32_range "${wal}" "${base}" 16 "${c0}")"
  [ "${c0}" -eq "${stored0}" ] && [ "${c1}" -eq "${stored1}" ]
}
