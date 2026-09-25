#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${DUEL_APP_ROOT:-/app}"
find "${APP_ROOT}/lib/duelctl" -type f -name '*.py' -exec sed -i 's/\r$//' {} +
find "${APP_ROOT}/scripts" -type f \( -name '*.sh' -o -name 'duelctl' \) -exec sed -i 's/\r$//' {} +
chmod +x "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/scripts/duelctl"
install -m 0755 "${APP_ROOT}/scripts/duelctl" "${APP_ROOT}/bin/duelctl"
python3 "${APP_ROOT}/fixtures/build_fixtures.py"
if [ -d /opt/verifier-fixtures/duelctl ]; then
  DUEL_HIDDEN_ROOT=/opt/verifier-fixtures/duelctl python3 "${APP_ROOT}/fixtures/build_fixtures.py"
fi
