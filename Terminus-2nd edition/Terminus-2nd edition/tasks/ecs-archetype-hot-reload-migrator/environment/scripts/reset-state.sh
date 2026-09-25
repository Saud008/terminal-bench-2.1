#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
TEMPLATES="${APP_ROOT}/data/templates"

rm -rf "${APP_ROOT}/data/chunks" "${APP_ROOT}/data/ecs_meta.db" "${APP_ROOT}/data/replay.journal.json"
mkdir -p "${APP_ROOT}/data/chunks" "${APP_ROOT}/output"

cp -f "${TEMPLATES}/hot_reload_alpha.db" "${APP_ROOT}/data/ecs_meta.db"
cp -a "${TEMPLATES}/hot_reload_alpha_chunks/." "${APP_ROOT}/data/chunks/"
cp -f "${TEMPLATES}/hot_reload_alpha.journal.json" "${APP_ROOT}/data/replay.journal.json"
