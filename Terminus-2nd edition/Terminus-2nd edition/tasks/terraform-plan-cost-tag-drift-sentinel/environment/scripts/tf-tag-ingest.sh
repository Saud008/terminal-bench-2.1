#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

plan=""
policy=""
staging="/app/state/plan-tag.stage"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan) plan="$2"; shift 2 ;;
    --policy) policy="$2"; shift 2 ;;
    --staging) staging="$2"; shift 2 ;;
    *) source "${APP_ROOT}/lib/common.sh"; die "unknown arg: $1" ;;
  esac
done

source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/staging.sh"

[[ -n "${plan}" && -f "${plan}" ]] || die "ingest requires readable --plan"
[[ -n "${policy}" && -f "${policy}" ]] || die "ingest requires readable --policy"

write_staging_snapshot "${plan}" "${policy}" "${staging}"
update_run_registry "${plan}"
echo "ingest ok: ${staging}"
