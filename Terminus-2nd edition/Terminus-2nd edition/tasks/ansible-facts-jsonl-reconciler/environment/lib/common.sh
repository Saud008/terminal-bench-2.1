#!/usr/bin/env bash
# Shared helpers for facts-chain modules.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
FACTS_DB="${FACTS_DB:-${APP_ROOT}/state/facts.db}"
STAGING_JSON="${APP_ROOT}/state/facts.staging.json"

die() {
  echo "facts-chain: $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [ -f "${path}" ] || die "file not found: ${path}"
}

ensure_facts_schema() {
  sqlite3 "${FACTS_DB}" <<'SQL'
CREATE TABLE IF NOT EXISTS hosts (
  inventory_uuid TEXT PRIMARY KEY,
  hostname TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS fact_snapshots (
  inventory_uuid TEXT NOT NULL,
  fact_key TEXT NOT NULL,
  fact_value TEXT NOT NULL,
  collected_at TEXT NOT NULL,
  PRIMARY KEY (inventory_uuid, fact_key)
);
CREATE TABLE IF NOT EXISTS fact_diffs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT NOT NULL,
  inventory_uuid TEXT NOT NULL,
  fact_key TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS run_meta (
  run_id TEXT PRIMARY KEY,
  source_lines INTEGER NOT NULL DEFAULT 0
);
SQL
}

snapshot_count() {
  sqlite3 "${FACTS_DB}" "SELECT COUNT(*) FROM fact_snapshots;"
}

diff_count_for_run() {
  local run_id="$1"
  sqlite3 "${FACTS_DB}" "SELECT COUNT(*) FROM fact_diffs WHERE run_id = '$(printf '%s' "${run_id}" | sed "s/'/''/g")';"
}

distinct_diff_keys_for_run() {
  local run_id="$1"
  sqlite3 "${FACTS_DB}" \
    "SELECT COUNT(DISTINCT inventory_uuid || char(9) || fact_key) FROM fact_diffs WHERE run_id = '$(printf '%s' "${run_id}" | sed "s/'/''/g")';"
}

record_source_lines() {
  local run_id="$1"
  local lines="$2"
  sqlite3 "${FACTS_DB}" \
    "INSERT OR REPLACE INTO run_meta (run_id, source_lines) VALUES ('$(printf '%s' "${run_id}" | sed "s/'/''/g")', ${lines});"
}

source_lines_for_run() {
  local run_id="$1"
  sqlite3 "${FACTS_DB}" \
    "SELECT COALESCE((SELECT source_lines FROM run_meta WHERE run_id = '$(printf '%s' "${run_id}" | sed "s/'/''/g")'), 0);"
}
