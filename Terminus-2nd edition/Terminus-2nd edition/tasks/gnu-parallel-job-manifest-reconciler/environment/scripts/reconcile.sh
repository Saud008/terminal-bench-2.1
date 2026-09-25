#!/usr/bin/env bash
# Reconcile GNU parallel joblog + .par logs into manifest.db.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/joblog.sh"
source "${APP_ROOT}/lib/parlog.sh"

joblog=""
par_dir=""
while [ $# -gt 0 ]; do
  case "$1" in
    --joblog) joblog="$2"; shift 2 ;;
    --par-dir) par_dir="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${joblog}" ] && [ -n "${par_dir}" ] || die "reconcile requires --joblog and --par-dir"

require_file "${joblog}"
require_dir "${par_dir}"

ensure_manifest_schema
load_joblog_into_db "${joblog}"
merge_par_into_db "${par_dir}"

echo "reconciled $(job_count_in_db) jobs"
