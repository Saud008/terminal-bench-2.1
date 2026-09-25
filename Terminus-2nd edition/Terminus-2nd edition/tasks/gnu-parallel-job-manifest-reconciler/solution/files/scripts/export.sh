#!/usr/bin/env bash
# Export parallel-export.json summary for a reconciled run.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/joblog.sh"
source "${APP_ROOT}/lib/parlog.sh"
source "${APP_ROOT}/lib/slots.sh"
source "${APP_ROOT}/lib/exitagg.sh"

joblog=""
par_dir=""
out=""
while [ $# -gt 0 ]; do
  case "$1" in
    --joblog) joblog="$2"; shift 2 ;;
    --par-dir) par_dir="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${joblog}" ] && [ -n "${par_dir}" ] && [ -n "${out}" ] || die "export requires --joblog, --par-dir, and --out"

require_file "${joblog}"
require_dir "${par_dir}"
[ -f "${STAGING_MANIFEST}" ] || die "missing staging manifest: ${STAGING_MANIFEST}"
[ -f "${MANIFEST_DB}" ] || die "run reconcile before export"

jobs="$(job_count_in_db)"
peak="$(peak_concurrency_from_pardir "${par_dir}")"
hist="$(exit_histogram_from_db)"
failed="$(failed_exit_count_from_db)"
cpu="$(par_cpu_seconds_total "${par_dir}")"

python3 - "${out}" "${jobs}" "${peak}" "${hist}" "${failed}" "${cpu}" <<'PY'
import json, sys
out, jobs, peak, hist, failed, cpu = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], int(sys.argv[5]), float(sys.argv[6])
doc = {
    "cpu_seconds": cpu,
    "exit_histogram": json.loads(hist),
    "failed_exit_count": failed,
    "job_count": jobs,
    "peak_concurrency": peak,
}
with open(out, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, sort_keys=True, separators=(",", ":"))
    fh.write("\n")
PY

echo "exported ${out}"
