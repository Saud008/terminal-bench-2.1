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
  sqlite3 "${OI_LEDGER_DB}" <<SQL
INSERT OR IGNORE INTO folder_cache(folder, uidvalidity, high_uid) VALUES('${folder}', ${uidvalidity}, 0);
UPDATE folder_cache SET uidvalidity=${uidvalidity} WHERE folder='${folder}';
SQL
}

oi_ledger_update_high() {
  local folder="$1"
  local high_uid="$2"
  sqlite3 "${OI_LEDGER_DB}" <<SQL
UPDATE folder_cache SET high_uid=${high_uid} WHERE folder='${folder}';
SQL
}

oi_ledger_read_high() {
  local folder="$1"
  sqlite3 "${OI_LEDGER_DB}" "SELECT high_uid FROM folder_cache WHERE folder='${folder}';"
}
