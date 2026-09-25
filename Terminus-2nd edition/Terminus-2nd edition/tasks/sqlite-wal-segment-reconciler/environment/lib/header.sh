#!/usr/bin/env bash
# WAL header parsing — page size offset must match /app/docs/wal-format.md
set -euo pipefail

WAL_PAGE_SIZE_OFFSET=12

wal_page_size() {
  local wal="$1"
  read_u32_be "${wal}" "${WAL_PAGE_SIZE_OFFSET}"
}

wal_salt_words() {
  local wal="$1"
  local s0 s1
  s0="$(read_u32_be "${wal}" 16)"
  s1="$(read_u32_be "${wal}" 20)"
  echo "${s0} ${s1}"
}

wal_frame_count() {
  local wal="$1"
  local psz size
  psz="$(wal_page_size "${wal}")"
  [ "${psz}" -gt 0 ] || return 1
  size="$(stat -c%s "${wal}")"
  echo $(( (size - 32) / (24 + psz) ))
}
