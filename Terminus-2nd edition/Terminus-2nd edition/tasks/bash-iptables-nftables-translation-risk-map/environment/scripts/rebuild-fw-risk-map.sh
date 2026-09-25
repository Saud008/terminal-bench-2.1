#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
for f in "${APP_ROOT}/scripts/fw-risk-map" "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/lib/"*.awk; do
  [ -f "$f" ] && sed -i 's/\r$//' "$f" 2>/dev/null || true
done
chmod +x "${APP_ROOT}/scripts/fw-risk-map" "${APP_ROOT}/lib/"*.sh 2>/dev/null || true
echo "rebuild ok"
