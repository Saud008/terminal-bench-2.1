#!/usr/bin/env bash
# Write /app/state/wal.stage staging snapshot beside the database.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/header.sh"

db=""
while [ $# -gt 0 ]; do
  case "$1" in
    --db) db="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${db}" ] || die "stage requires --db"

wal="$(wal_path_for "${db}")"
require_db "${db}"
restore_wal_snapshot "${db}"
[ -f "${wal}" ] || die "wal file missing: ${wal}"

stagedir="$(state_dir_for "${db}")"
out="${stagedir}/wal.stage"
psz="$(wal_page_size "${wal}")"
frames="$(wal_frame_count "${wal}")"

python3 - "${out}" "${psz}" "${frames}" <<'PY'
import json, sys
out, psz, frames = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
doc = {
    "page_size": psz,
    "frame_count": frames,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

echo "staged ${out}"
