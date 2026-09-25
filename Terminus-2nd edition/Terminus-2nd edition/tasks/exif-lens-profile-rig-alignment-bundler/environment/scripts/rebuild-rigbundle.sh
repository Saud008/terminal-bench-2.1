#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
chmod +x "${APP_ROOT}/bin/rigbundle" "${APP_ROOT}/scripts/"*.sh 2>/dev/null || true
find "${APP_ROOT}/lib" -name '*.sh' -exec chmod +x {} + 2>/dev/null || true
echo "rigbundle rebuild ok"
