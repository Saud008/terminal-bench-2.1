#!/usr/bin/env bash
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
read -r salt1 salt2 <<<"$(wal_salt_words "${wal}")"

python3 - "${out}" "${psz}" "${frames}" "${salt1}" "${salt2}" <<'PY'
import json, sys
out, psz, frames, salt1, salt2 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
doc = {
    "frame_count": frames,
    "page_size": psz,
    "salt1": salt1,
    "salt2": salt2,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

echo "staged ${out}"
