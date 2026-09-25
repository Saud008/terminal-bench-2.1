#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
PATCHES="$(cd "$(dirname "$0")/patches" && pwd)"

for f in common parse_readings lab_delta paper_lineage intent_policy profile_checksum ticket_epoch staging export_report; do
  cp -f "${PATCHES}/${f}.sh" "${APP_ROOT}/lib/${f}.sh"
done
cp -f "${PATCHES}/icc-ingest.sh" "${APP_ROOT}/scripts/icc-ingest.sh"
cp -f "${PATCHES}/icc-evaluate.sh" "${APP_ROOT}/scripts/icc-evaluate.sh"
cp -f "${PATCHES}/icc-export.sh" "${APP_ROOT}/scripts/icc-export.sh"
cp -f "${PATCHES}/rebuild-bundler.sh" "${APP_ROOT}/scripts/rebuild-bundler.sh"
cp -f "${PATCHES}/icc-drift-bundler" "${APP_ROOT}/bin/icc-drift-bundler"
chmod +x "${APP_ROOT}/lib/"*.sh "${APP_ROOT}/lib/decoy/"*.sh "${APP_ROOT}/scripts/"*.sh "${APP_ROOT}/bin/icc-drift-bundler"
bash "${APP_ROOT}/scripts/rebuild-bundler.sh"
mkdir -p /app/output /app/state
