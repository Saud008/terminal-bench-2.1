#!/usr/bin/env bash
set -euo pipefail
# Verifier rebuild hook — sentinel is interpreted; refresh line endings only.
APP_ROOT="${APP_ROOT:-/app}"
for f in "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/cvls-governor"; do
  [ -f "$f" ] && sed -i 's/\r$//' "$f" 2>/dev/null || true
done
chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/scripts/cvls-governor" 2>/dev/null || true
test -x /usr/local/bin/cvls-governor
