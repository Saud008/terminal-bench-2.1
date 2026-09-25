#!/usr/bin/env bash
# Shared helpers for par-chain modules.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
MANIFEST_DB="${APP_ROOT}/state/manifest.db"
STAGING_MANIFEST="${APP_ROOT}/state/job.manifest.json"
USER_HZ=100

die() {
  echo "par-chain: $*" >&2
  exit 1
}

require_file() {
  local path="$1"
  [ -f "${path}" ] || die "file not found: ${path}"
}

require_dir() {
  local path="$1"
  [ -d "${path}" ] || die "directory not found: ${path}"
}

ensure_manifest_schema() {
  sqlite3 "${MANIFEST_DB}" <<'SQL'
CREATE TABLE IF NOT EXISTS jobs (
  seq INTEGER PRIMARY KEY,
  host TEXT NOT NULL,
  exitval INTEGER NOT NULL,
  command TEXT NOT NULL,
  slot INTEGER,
  utime_jiffies INTEGER,
  stime_jiffies INTEGER,
  wall_sec REAL,
  start_epoch REAL,
  end_epoch REAL
);
SQL
}

job_count_in_db() {
  sqlite3 "${MANIFEST_DB}" "SELECT COUNT(*) FROM jobs;"
}

distinct_job_count_in_db() {
  sqlite3 "${MANIFEST_DB}" "SELECT COUNT(DISTINCT seq) FROM jobs;"
}
