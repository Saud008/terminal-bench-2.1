#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${ROSTER_APP_ROOT:-/app}"
find "${APP_ROOT}/lib/roster" -type f -name '*.py' -exec sed -i 's/\r$//' {} +
find "${APP_ROOT}/scripts" -type f \( -name '*.sh' -o -name 'rosterctl' \) -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/scripts/rosterctl"
install -m 0755 "${APP_ROOT}/scripts/rosterctl" "${APP_ROOT}/bin/rosterctl"
if [ -d /opt/verifier-fixtures/rosterctl ]; then
  ROSTER_HIDDEN_ROOT=/opt/verifier-fixtures/rosterctl python3 "${APP_ROOT}/fixtures/build_fixtures.py"
fi
