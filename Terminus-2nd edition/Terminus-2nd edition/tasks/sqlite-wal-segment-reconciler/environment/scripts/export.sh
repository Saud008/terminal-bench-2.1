#!/usr/bin/env bash
# Export wal-report.json summary for a reconciled database.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/header.sh"

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

wal="$(wal_path_for "${db}")"
require_db "${db}"
restore_wal_snapshot "${db}"
[ -f "${wal}" ] || die "wal file missing: ${wal}"
stage="$(state_dir_for "${db}")/wal.stage"
[ -f "${stage}" ] || die "missing staging snapshot: ${stage}"

psz="$(wal_page_size "${wal}")"
frames="$(wal_frame_count "${wal}")"
max_frame_id="${frames}"
applied_rows="$(sqlite3 "${db}" "SELECT COUNT(*) FROM entries;" 2>/dev/null || echo 0)"

python3 - "${out}" "${psz}" "${max_frame_id}" "${applied_rows}" <<'PY'
import json, sys
out, psz, max_fid, entry_rows = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
doc = {
    "page_size": psz,
    "applied_frame_count": max_fid,
    "entry_row_count": entry_rows,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

echo "exported ${out}"
