#!/usr/bin/env bash
# Forecast calendar drift and missed runs into stage manifest.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

bundle=""
context_file=""
reference_now=""
while [ $# -gt 0 ]; do
  case "$1" in
    --bundle) bundle="$2"; shift 2 ;;
    --context) context_file="$2"; shift 2 ;;
    --now) reference_now="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${bundle}" ] && [ -n "${context_file}" ] && [ -n "${reference_now}" ] || die "forecast requires --bundle --context --now"
require_dir "${bundle}"
require_file "${context_file}"

timer_name="$(bundle_timer_name "${bundle}")"
manifest="$(manifest_path_for "${bundle}")"
require_file "${manifest}"

python3 -m lib.forecast.runner forecast "${bundle}" "${timer_name}" "${context_file}" "${reference_now}" "${manifest}"
echo "forecast ${manifest}"
