#!/usr/bin/env bash

RF_APP_ROOT="${RF_APP_ROOT:-/app}"
RF_INDEX_DB="${RF_INDEX_DB:-${RF_APP_ROOT}/state/fuzzy-index.db}"

rf_ensure_index() {
  mkdir -p "$(dirname "${RF_INDEX_DB}")"
  sqlite3 "${RF_INDEX_DB}" <<'SQL'
CREATE TABLE IF NOT EXISTS fuzzy_hashes (
  hash TEXT NOT NULL,
  mail_id TEXT NOT NULL,
  shingle TEXT NOT NULL,
  key_epoch INTEGER NOT NULL,
  checksum_algo_id INTEGER NOT NULL,
  PRIMARY KEY (hash, mail_id, shingle)
);
SQL
}

rf_index_rotate_epoch() {
  local key_epoch="$1"
  local checksum_algo_id="$2"
  rf_ensure_index
  sqlite3 "${RF_INDEX_DB}" <<SQL
UPDATE fuzzy_hashes SET key_epoch=${key_epoch};
SQL
}

rf_index_insert_shingle() {
  local hash="$1"
  local mail_id="$2"
  local shingle="$3"
  local key_epoch="$4"
  local checksum_algo_id="$5"
  sqlite3 "${RF_INDEX_DB}" <<SQL
INSERT OR REPLACE INTO fuzzy_hashes(hash, mail_id, shingle, key_epoch, checksum_algo_id)
VALUES('${hash}', '${mail_id}', '${shingle}', ${key_epoch}, ${checksum_algo_id});
SQL
}

rf_index_distinct_hashes() {
  rf_ensure_index
  sqlite3 "${RF_INDEX_DB}" "SELECT COUNT(DISTINCT hash) FROM fuzzy_hashes;"
}

rf_index_row_count() {
  rf_ensure_index
  sqlite3 "${RF_INDEX_DB}" "SELECT COUNT(*) FROM fuzzy_hashes;"
}

rf_index_clear() {
  rf_ensure_index
  sqlite3 "${RF_INDEX_DB}" "DELETE FROM fuzzy_hashes;"
}
