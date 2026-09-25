#!/usr/bin/env bash
# Parse GNU parallel --joblog TSV files.
set -euo pipefail

joblog_row_count() {
  local joblog="$1"
  awk 'NR > 1 && NF >= 8 { c++ } END { print c + 0 }' "${joblog}"
}

joblog_each_row() {
  local joblog="$1"
  awk -F'\t' 'NR > 1 && NF >= 9 {
    printf "%s\t%s\t%s\t%s\n", $1, $2, $7, $9
  }' "${joblog}"
}

load_joblog_into_db() {
  local joblog="$1"
  while IFS=$'\t' read -r seq host exitval command; do
    [ -n "${seq}" ] || continue
    sqlite3 "${MANIFEST_DB}" \
      "INSERT OR IGNORE INTO jobs (seq, host, exitval, command) VALUES (${seq}, '$(printf '%s' "${host}" | sed "s/'/''/g")', ${exitval}, '$(printf '%s' "${command}" | sed "s/'/''/g")');"
  done < <(joblog_each_row "${joblog}")
}
