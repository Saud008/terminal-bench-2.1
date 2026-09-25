#!/usr/bin/env bash
# Export normalized SEL CSV from SQLite database.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

db=""
out=""
while [ $# -gt 0 ]; do
  case "$1" in
    --db) db="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${db}" ] && [ -n "${out}" ] || die "export requires --db and --out"
require_db "${db}"

stage="$(stage_path_for "${db}")"
[ -f "${stage}" ] || die "missing staging snapshot: ${stage}"

mkdir -p "$(dirname "${out}")"

{
  echo "record_id,timestamp_iso,sensor_type_hex,sensor_name,severity,event_type_hex"
  sqlite3 -separator '|' "${db}" "
    SELECT record_id, ts, sensor_type, sensor_name, severity, event_type
    FROM sel_records
    ORDER BY ts DESC, record_id ASC;
  " | while IFS='|' read -r rid ts stype sname sev etype; do
    hex_stype="$(printf '0x%02X' "${stype}")"
    hex_etype="$(printf '0x%02X' "${etype}")"
    iso="$(ts_to_iso "${ts}")"
    echo "${rid},${iso},${hex_stype},${sname},${sev},${hex_etype}"
  done
} > "${out}"

echo "exported ${out}"
