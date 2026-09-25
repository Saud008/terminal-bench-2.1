#!/usr/bin/env bash

OI_APP_ROOT="${OI_APP_ROOT:-/app}"
OI_STATE_DIR="${OI_STATE_DIR:-${OI_APP_ROOT}/state}"
OI_LEDGER_DB="${OI_LEDGER_DB:-${OI_STATE_DIR}/sync-ledger.db}"

oi_ensure_ledger() {
  mkdir -p "${OI_STATE_DIR}"
  sqlite3 "${OI_LEDGER_DB}" <<'SQL'
CREATE TABLE IF NOT EXISTS folder_cache (
  folder TEXT PRIMARY KEY,
  uidvalidity INTEGER NOT NULL,
  high_uid INTEGER NOT NULL
);
SQL
}

oi_ledger_prepare_folder() {
  local folder="$1"
  local uidvalidity="$2"
  oi_ensure_ledger
  local stored
  stored="$(sqlite3 "${OI_LEDGER_DB}" "SELECT uidvalidity FROM folder_cache WHERE folder='${folder}';" 2>/dev/null || true)"
  if [[ -z "${stored}" ]]; then
    sqlite3 "${OI_LEDGER_DB}" "INSERT INTO folder_cache(folder, uidvalidity, high_uid) VALUES('${folder}', ${uidvalidity}, 0);"
  elif [[ "${stored}" != "${uidvalidity}" ]]; then
    sqlite3 "${OI_LEDGER_DB}" "DELETE FROM folder_cache WHERE folder='${folder}';"
    sqlite3 "${OI_LEDGER_DB}" "INSERT INTO folder_cache(folder, uidvalidity, high_uid) VALUES('${folder}', ${uidvalidity}, 0);"
  fi
}

oi_ledger_update_high() {
  local folder="$1"
  local high_uid="$2"
  sqlite3 "${OI_LEDGER_DB}" "UPDATE folder_cache SET high_uid=${high_uid} WHERE folder='${folder}';"
}

oi_ledger_read_high() {
  local folder="$1"
  sqlite3 "${OI_LEDGER_DB}" "SELECT high_uid FROM folder_cache WHERE folder='${folder}';"
}
