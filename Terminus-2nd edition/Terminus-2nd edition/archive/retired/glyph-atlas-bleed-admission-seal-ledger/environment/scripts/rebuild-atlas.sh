#!/usr/bin/env bash
# Verifier rebuild hook — normalize line endings and reinstall atlasd before pytest.
set -euo pipefail
APP_ROOT="${ATLAS_APP_ROOT:-/app}"
find "${APP_ROOT}/lib/atlas" -type f -name '*.py' -exec sed -i 's/\r$//' {} +
find "${APP_ROOT}/scripts" -type f \( -name '*.sh' -o -name 'atlasd' \) -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/scripts/atlasd" 2>/dev/null || true
install -m 0755 "${APP_ROOT}/scripts/atlasd" "${APP_ROOT}/bin/atlasd"
chmod +x "${APP_ROOT}/bin/atlasd"
