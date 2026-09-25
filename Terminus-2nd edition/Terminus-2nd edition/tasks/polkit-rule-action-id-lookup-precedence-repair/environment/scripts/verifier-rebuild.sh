#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
find "${APP_ROOT}/lib" -name '*.sh' -exec sed -i 's/\r$//' {} + 2>/dev/null || true
chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/bin/pkctl" 2>/dev/null || true
echo "pkctl rebuild ok"
