#!/usr/bin/env bash
# Write drift report JSON from stage manifest forecast block.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
source "${APP_ROOT}/lib/common.sh"

bundle=""
out=""
while [ $# -gt 0 ]; do
  case "$1" in
    --bundle) bundle="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    *) die "unknown arg: $1" ;;
  esac
done
[ -n "${bundle}" ] && [ -n "${out}" ] || die "write-report requires --bundle and --out"
require_dir "${bundle}"

manifest="$(manifest_path_for "${bundle}")"
require_file "${manifest}"
mkdir -p "$(dirname "${out}")"

python3 -m lib.forecast.runner write-report "${manifest}" "${out}"
echo "exported ${out}"
