#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
PATCHES="$(cd "$(dirname "$0")/patches" && pwd)"

for f in wal_name timeline continuity partial label target digest staging plan; do
  cp -f "${PATCHES}/${f}.sh" "${APP_ROOT}/lib/${f}.sh"
done
chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/lib/ingest/"*.sh "${APP_ROOT}/lib/export/"*.sh "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/bin/walplan"
bash "${APP_ROOT}/scripts/rebuild-walplan.sh"
