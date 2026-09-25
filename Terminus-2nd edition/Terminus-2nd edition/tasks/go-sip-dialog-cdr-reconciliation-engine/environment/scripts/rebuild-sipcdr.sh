#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${SIPCDR_APP_ROOT:-/app}"
find "${APP_ROOT}/lib/sipcdr" -type f -name '*.py' -exec sed -i 's/\r$//' {} +
find "${APP_ROOT}/scripts" -type f \( -name '*.sh' -o -name 'sipcdrctl' \) -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/scripts/sipcdrctl"
install -m 0755 "${APP_ROOT}/scripts/sipcdrctl" "${APP_ROOT}/bin/sipcdrctl"
python3 "${APP_ROOT}/fixtures/build_fixtures.py"
if [ -d /opt/verifier-fixtures/sipcdrctl ]; then
  SIPCDR_HIDDEN_ROOT=/opt/verifier-fixtures/sipcdrctl python3 "${APP_ROOT}/fixtures/build_fixtures.py"
fi
