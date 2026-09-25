#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export APP_ROOT

staging=""
policy=""
out="/app/output/tag-violations.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging) staging="$2"; shift 2 ;;
    --policy) policy="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) source "${APP_ROOT}/lib/common.sh"; die "unknown arg: $1" ;;
  esac
done

source "${APP_ROOT}/lib/common.sh"
source "${APP_ROOT}/lib/report.sh"

[[ -n "${staging}" && -f "${staging}" ]] || die "audit requires readable --staging"
[[ -n "${policy}" && -f "${policy}" ]] || die "audit requires readable --policy"

deny_count="$(write_violation_report "${staging}" "${policy}" "${out}")"
if [[ "${deny_count}" -gt 0 ]]; then
  exit 2
fi
exit 0
