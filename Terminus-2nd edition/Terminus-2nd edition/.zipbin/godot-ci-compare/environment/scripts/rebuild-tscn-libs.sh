#!/usr/bin/env bash
# Verifier rebuild hook — normalize line endings on tscn libs before pytest.
set -euo pipefail
APP_ROOT="${TSCN_APP_ROOT:-/app}"
find "${APP_ROOT}/lib/tscn" -type f -name '*.sh' -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/bin/tscn-merge" "${APP_ROOT}/lib/tscn/"*.sh "${APP_ROOT}/scripts/"*.sh 2>/dev/null || true
