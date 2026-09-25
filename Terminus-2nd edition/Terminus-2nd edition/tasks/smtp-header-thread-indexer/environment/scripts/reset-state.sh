#!/usr/bin/env bash
set -euo pipefail

APP="/app"
DB="${APP}/data/thread.db"
BACKUP="${APP}/data/thread.db.bak"
OUT="${APP}/output"

if [[ -f "${BACKUP}" ]]; then
  cp -f "${BACKUP}" "${DB}"
else
  sqlite3 "${DB}" < "${APP}/data/schema.sql"
  cp -f "${DB}" "${BACKUP}"
fi

rm -rf "${OUT}"
mkdir -p "${OUT}"
rm -f "${APP}/state/thread-index.snapshot.json"
mkdir -p "${APP}/state"
