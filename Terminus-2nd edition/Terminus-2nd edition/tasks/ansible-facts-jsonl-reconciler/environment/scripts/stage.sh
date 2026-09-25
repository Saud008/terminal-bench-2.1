#!/usr/bin/env bash
# Write /app/state/facts.staging.json staging snapshot.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/schema.sh"

run_id=""
while [ $# -gt 0 ]; do
  case "$1" in
    --run-id) run_id="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${run_id}" ] || die "stage requires --run-id"

[ -f "${FACTS_DB}" ] || die "run reconcile before stage"

out="${STAGING_JSON}"
doc="$(build_staging_document "${run_id}")"

printf '%s\n' "${doc}" > "${out}"
validate_staging_schema "${out}" "${run_id}" || die "staging schema validation failed"

echo "staged ${out}"
