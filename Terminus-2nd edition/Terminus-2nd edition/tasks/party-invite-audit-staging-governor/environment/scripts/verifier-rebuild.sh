#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${PARTY_APP_ROOT:-/app}"
find "${APP_ROOT}/lib/party" -type f -name '*.py' -exec sed -i 's/\r$//' {} +
find "${APP_ROOT}/scripts" -type f \( -name '*.sh' -o -name 'partyd' -o -name '*.py' \) -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/scripts/partyd"
install -m 0755 "${APP_ROOT}/scripts/partyd" "${APP_ROOT}/bin/partyd"
