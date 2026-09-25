#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCHES="${SCRIPT_DIR}/files"

cp "${PATCHES}/exif_time.sh" "${APP_ROOT}/lib/time/exif_time.sh"
cp "${PATCHES}/lens_match.sh" "${APP_ROOT}/lib/lens/lens_match.sh"
cp "${PATCHES}/frame_gap.sh" "${APP_ROOT}/lib/gap/frame_gap.sh"
cp "${PATCHES}/rig_slot.sh" "${APP_ROOT}/lib/rig/rig_slot.sh"
cp "${PATCHES}/checker_gate.sh" "${APP_ROOT}/lib/checker/checker_gate.sh"
cp "${PATCHES}/staging_io.sh" "${APP_ROOT}/lib/staging/staging_io.sh"
cp "${PATCHES}/export.sh" "${APP_ROOT}/scripts/export.sh"

for copied in \
  "${APP_ROOT}/lib/time/exif_time.sh" \
  "${APP_ROOT}/lib/lens/lens_match.sh" \
  "${APP_ROOT}/lib/gap/frame_gap.sh" \
  "${APP_ROOT}/lib/rig/rig_slot.sh" \
  "${APP_ROOT}/lib/checker/checker_gate.sh" \
  "${APP_ROOT}/lib/staging/staging_io.sh" \
  "${APP_ROOT}/scripts/export.sh"; do
  sed -i 's/\r$//' "${copied}"
done

make -C "${APP_ROOT}" install
bash "${APP_ROOT}/scripts/reset-state.sh"
test -x /app/bin/rigbundle
echo "exif-rig-bundler oracle ready"
