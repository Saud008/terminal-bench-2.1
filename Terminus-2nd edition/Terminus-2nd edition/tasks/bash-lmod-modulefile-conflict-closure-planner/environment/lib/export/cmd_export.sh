#!/bin/bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"

staging=""
out=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --staging) staging="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "${staging}" && -n "${out}" ]] || { echo "need --staging and --out" >&2; exit 2; }

# shellcheck source=/dev/null
source "${APP_ROOT}/lib/export/export_plan.sh"
write_load_plan_json "${staging}" "${out}"
