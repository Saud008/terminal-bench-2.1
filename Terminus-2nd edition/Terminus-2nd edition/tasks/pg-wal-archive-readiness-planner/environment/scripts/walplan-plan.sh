#!/usr/bin/env bash
# Export restore readiness planner JSON from staging.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/plan.sh"
source "${APP_ROOT}/lib/export/helpers.sh"

staging=""
out=""
restore_target=""
config_root="/app/config"
if [[ -n "${TB3_CLOCK_ROOT:-}" ]]; then
  config_root="${TB3_CLOCK_ROOT}"
fi
while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging) staging="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    --restore-target) restore_target="$2"; shift 2 ;;
    --config-root) config_root="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[[ -n "${staging}" && -n "${out}" && -n "${restore_target}" ]] || die "plan requires --staging --out --restore-target"
validate_export_paths "${staging}" "${out}"
code="$(write_restore_plan "${staging}" "${out}" "${restore_target}" "${config_root}")"
exit "${code}"
