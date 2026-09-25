#!/usr/bin/env bash
# Verifier rebuild hook — normalize line endings and reinstall sheetd before pytest.
set -euo pipefail
APP_ROOT="${SHEET_APP_ROOT:-/app}"
find "${APP_ROOT}/lib/sheet" -type f -name '*.py' -exec sed -i 's/\r$//' {} +
find "${APP_ROOT}/scripts" -type f \( -name '*.sh' -o -name 'sheetd' \) -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/scripts/sheetd" 2>/dev/null || true
install -m 0755 "${APP_ROOT}/scripts/sheetd" "${APP_ROOT}/bin/sheetd"
chmod +x "${APP_ROOT}/bin/sheetd"
