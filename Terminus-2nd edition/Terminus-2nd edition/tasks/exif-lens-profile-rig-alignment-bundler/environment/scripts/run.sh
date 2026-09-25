#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
exif=""
mount=""
lenses=""
checkerboard=""
while [ $# -gt 0 ]; do
  case "$1" in
    --exif) exif="$2"; shift 2 ;;
    --mount) mount="$2"; shift 2 ;;
    --lenses) lenses="$2"; shift 2 ;;
    --checkerboard) checkerboard="$2"; shift 2 ;;
    *) source "${APP_ROOT}/lib/core/common.sh"; die "unknown arg: $1" ;;
  esac
done
source "${APP_ROOT}/lib/core/common.sh"
[ -n "${exif}" ] && [ -n "${mount}" ] && [ -n "${lenses}" ] && [ -n "${checkerboard}" ] || die "run requires --exif --mount --lenses --checkerboard"
bash "${APP_ROOT}/scripts/ingest.sh" --exif "${exif}" --mount "${mount}"
bash "${APP_ROOT}/scripts/align.sh" --lenses "${lenses}" --checkerboard "${checkerboard}"
bash "${APP_ROOT}/scripts/export.sh"
