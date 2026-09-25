#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
chmod +x "${APP_ROOT}/scripts/edl-conform-audit" "${APP_ROOT}/lib/"*.sh 2>/dev/null || true
sed -i 's/\r$//' "${APP_ROOT}/scripts/edl-conform-audit" "${APP_ROOT}/lib/"*.sh 2>/dev/null || true
install -m 0755 "${APP_ROOT}/scripts/edl-conform-audit" /usr/local/bin/edl-conform-audit
echo "edl-conform-audit rebuilt"
