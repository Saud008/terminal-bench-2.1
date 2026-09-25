#!/usr/bin/env bash
# Ingest binary SEL blob into SQLite staging database.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/parse.sh"
source "${APP_ROOT}/lib/checksum.sh"
source "${APP_ROOT}/lib/sensor_map.sh"
source "${APP_ROOT}/lib/staging.sh"

input=""
db=""
while [ $# -gt 0 ]; do
  case "$1" in
    --input) input="$2"; shift 2 ;;
    --db) db="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${input}" ] && [ -n "${db}" ] || die "ingest requires --input and --db"
[ -f "${input}" ] || die "input not found: ${input}"

mkdir -p "$(dirname "${db}")"
ensure_schema "${db}"

read -r rec_count rec_len <<<"$(parse_sel_header "${input}")" || die "invalid sel header"
stride="$(record_stride "${rec_len}")"

digest="$(sha256sum "${input}" | awk '{print $1}')"
accepted=0
rejected=0
dup=0
offset=8

for ((i = 0; i < rec_count; i++)); do
  read -r rid rtype ts gen _rev stype snum etype sev <<<"$(parse_record_fields "${input}" "${offset}")"

  if [ "${rtype}" -ne 2 ]; then
    offset=$((offset + stride))
    continue
  fi

  if record_exists "${db}" "${rid}"; then
    dup=$((dup + 1))
    offset=$((offset + stride))
    continue
  fi

  if ! verify_record_checksum "${input}" "${offset}" "${rec_len}"; then
    rejected=$((rejected + 1))
    offset=$((offset + stride))
    continue
  fi

  sname="$(sensor_name_for "${stype}")"
  insert_sel_record "${db}" "${rid}" "${rtype}" "${ts}" "${gen}" "${stype}" "${snum}" "${etype}" "${sev}" "${sname}"
  accepted=$((accepted + 1))
  offset=$((offset + stride))
done

stage_out="$(stage_path_for "${db}")"
write_stage_snapshot "${stage_out}" "${accepted}" "${rejected}" "${dup}" "${digest}"
echo "ingested ${accepted} records"
