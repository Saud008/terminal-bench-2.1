#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${SNAPRET_APP_ROOT:-/app}"
python3 "${APP_ROOT}/fixtures/build_fixtures.py"
if [ -d /opt/verifier-fixtures/snapretctl ]; then
  SNAPRET_HIDDEN_ROOT=/opt/verifier-fixtures/snapretctl python3 "${APP_ROOT}/fixtures/build_fixtures.py"
fi
find "${APP_ROOT}/lib/snapret" -type f -name '*.py' -exec sed -i 's/\r$//' {} +
find "${APP_ROOT}/scripts" -type f \( -name '*.sh' -o -name 'snapretctl' \) -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/scripts/snapretctl"
mkdir -p "${APP_ROOT}/bin"
install -m 0755 "${APP_ROOT}/scripts/snapretctl" "${APP_ROOT}/bin/snapretctl"
