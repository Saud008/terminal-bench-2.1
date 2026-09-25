#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${MUSDOSS_APP_ROOT:-/app}"
find "${APP_ROOT}/lib/musdoss" -type f -name '*.py' -exec sed -i 's/\r$//' {} +
find "${APP_ROOT}/scripts" -type f \( -name '*.sh' -o -name 'musdoss' \) -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/scripts/musdoss"
install -m 0755 "${APP_ROOT}/scripts/musdoss" /usr/local/bin/musdoss
