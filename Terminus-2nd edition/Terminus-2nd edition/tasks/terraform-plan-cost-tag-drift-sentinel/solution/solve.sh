#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
PATCHES="$(cd "$(dirname "$0")/patches" && pwd)"

for f in common parse_plan alias inherit moved unknowns policy staging report; do
  cp -f "${PATCHES}/${f}.sh" "${APP_ROOT}/lib/${f}.sh"
done
cp -f "${PATCHES}/emit.sh" "${APP_ROOT}/lib/export/emit.sh"
cp -f "${PATCHES}/legacy_flatten.sh" "${APP_ROOT}/lib/decoy/legacy_flatten.sh"
cp -f "${PATCHES}/tf-tag-ingest.sh" "${APP_ROOT}/scripts/tf-tag-ingest.sh"
cp -f "${PATCHES}/tf-tag-audit.sh" "${APP_ROOT}/scripts/tf-tag-audit.sh"
cp -f "${PATCHES}/rebuild-sentinel.sh" "${APP_ROOT}/scripts/rebuild-sentinel.sh"
cp -f "${PATCHES}/tf-tag-sentinel" "${APP_ROOT}/bin/tf-tag-sentinel"
chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/lib/decoy/"*.sh "${APP_ROOT}/lib/export/"*.sh "${APP_ROOT}/stage/"*.sh "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/bin/tf-tag-sentinel"
bash "${APP_ROOT}/scripts/rebuild-sentinel.sh"
