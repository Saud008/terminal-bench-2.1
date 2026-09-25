#!/usr/bin/env bash
# Load timer unit bundle into stage manifest.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

bundle=""
timer_name=""
while [ $# -gt 0 ]; do
  case "$1" in
    --bundle) bundle="$2"; shift 2 ;;
    --timer-name) timer_name="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${bundle}" ] && [ -n "${timer_name}" ] || die "load requires --bundle and --timer-name"
require_dir "${bundle}"

manifest="$(manifest_path_for "${bundle}")"
mkdir -p "$(dirname "${manifest}")"
python3 -m lib.forecast.runner load "${bundle}" "${timer_name}" "${manifest}"
echo "loaded ${manifest}"
