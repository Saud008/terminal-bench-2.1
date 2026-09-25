#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/header.sh"
source "${APP_ROOT}/lib/checksum.sh"
source "${APP_ROOT}/lib/frames.sh"

db=""
while [ $# -gt 0 ]; do
  case "$1" in
    --db) db="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${db}" ] || die "reconcile requires --db"

wal="$(wal_path_for "${db}")"
require_db "${db}"
restore_wal_snapshot "${db}"
[ -f "${wal}" ] || die "wal file missing: ${wal}"

ensure_meta_schema "${db}"
restore_wal_snapshot "${db}"
[ -f "${wal}" ] || die "wal file missing after schema init: ${wal}"

psz="$(wal_page_size "${wal}")"
frames="$(wal_frame_count "${wal}")"
read -r salt0 salt1 <<<"$(wal_salt_words "${wal}")"
s0="${salt0}"
s1="${salt1}"

applied=0
for ((fid = 1; fid <= frames; fid++)); do
  restore_wal_snapshot "${db}"
  verify_frame_checksum "${wal}" "${fid}" "${psz}" "${s0}" "${s1}" || die "checksum failed frame ${fid}"
  page_no="$(frame_page_no "${wal}" "${fid}" "${psz}")"
  apply_frame_record "${db}" "${fid}" "${page_no}"
done

restore_wal_snapshot "${db}"

echo "reconciled ${applied} new frames"
