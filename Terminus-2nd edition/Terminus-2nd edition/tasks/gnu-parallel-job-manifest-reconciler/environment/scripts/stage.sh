#!/usr/bin/env bash
# Write /app/state/job.manifest.json staging snapshot.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/joblog.sh"
source "${APP_ROOT}/lib/parlog.sh"
source "${APP_ROOT}/lib/slots.sh"
source "${APP_ROOT}/lib/exitagg.sh"

joblog=""
par_dir=""
while [ $# -gt 0 ]; do
  case "$1" in
    --joblog) joblog="$2"; shift 2 ;;
    --par-dir) par_dir="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${joblog}" ] && [ -n "${par_dir}" ] || die "stage requires --joblog and --par-dir"

require_file "${joblog}"
require_dir "${par_dir}"
[ -f "${MANIFEST_DB}" ] || die "run reconcile before stage"

out="${STAGING_MANIFEST}"
jobs="$(joblog_row_count "${joblog}")"
peak="$(peak_concurrency_from_pardir "${par_dir}")"
hist="$(joblog_exit_histogram "${joblog}")"
parsed=0

python3 - "${out}" "${jobs}" "${peak}" "${hist}" "${parsed}" <<'PY'
import json, sys
out, jobs, peak, hist, parsed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5])
doc = {
    "exit_histogram": json.loads(hist),
    "job_count": jobs,
    "par_files_parsed": parsed,
    "peak_concurrency": peak,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

parsed="$(par_file_count "${par_dir}")"
peak="$(peak_concurrency_from_pardir "${par_dir}")"
hist="$(par_exit_histogram "${par_dir}")"

echo "staged ${out} (${parsed} par files scanned)"
