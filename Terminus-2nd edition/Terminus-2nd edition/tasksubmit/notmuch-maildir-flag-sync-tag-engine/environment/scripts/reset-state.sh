#!/usr/bin/env bash
set -euo pipefail

APP="/app"
DB="${APP}/data/mailsync.db"
BACKUP="${APP}/data/mailsync.db.bak"
OUT="${APP}/output"
MAILDIR="${APP}/fixtures/maildir"
TB3="/opt/verifier-fixtures/maildir"

if [[ -f "${BACKUP}" ]]; then
  cp -f "${BACKUP}" "${DB}"
else
  sqlite3 "${DB}" < "${APP}/data/schema.sql"
  cp -f "${DB}" "${BACKUP}"
fi

rm -rf "${OUT}"
mkdir -p "${OUT}" "${APP}/state"

rm -rf "${MAILDIR}/cur" "${MAILDIR}/new"
mkdir -p "${MAILDIR}/cur" "${MAILDIR}/new" "${MAILDIR}/tmp"
cp -a "${APP}/fixtures/.maildir-seed/cur/." "${MAILDIR}/cur/"
cp -a "${APP}/fixtures/.maildir-seed/new/." "${MAILDIR}/new/"

rm -f "${APP}/state/mail-sync.snapshot.json"

if [[ -d "${APP}/opt-verifier-fixtures/.maildir-seed" ]]; then
  rm -rf "${TB3}/cur" "${TB3}/new"
  mkdir -p "${TB3}/cur" "${TB3}/new"
  cp -a "${APP}/opt-verifier-fixtures/.maildir-seed/cur/." "${TB3}/cur/"
  cp -a "${APP}/opt-verifier-fixtures/.maildir-seed/new/." "${TB3}/new/"
fi
