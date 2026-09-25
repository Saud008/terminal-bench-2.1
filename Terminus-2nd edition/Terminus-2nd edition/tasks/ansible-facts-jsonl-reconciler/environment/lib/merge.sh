#!/usr/bin/env bash
# Merge JSONL fact rows into facts.db.
set -euo pipefail

merge_fact_row() {
  local host_key="$1"
  local hostname="$2"
  local fact_key="$3"
  local fact_value="$4"
  local collected_at="$5"
  local run_id="$6"

  sqlite3 "${FACTS_DB}" \
    "INSERT OR REPLACE INTO hosts (inventory_uuid, hostname) VALUES ('$(printf '%s' "${host_key}" | sed "s/'/''/g")', '$(printf '%s' "${hostname}" | sed "s/'/''/g")');"

  local existing
  existing="$(sqlite3 "${FACTS_DB}" \
    "SELECT fact_value || char(9) || collected_at FROM fact_snapshots WHERE inventory_uuid = '$(printf '%s' "${host_key}" | sed "s/'/''/g")' AND fact_key = '$(printf '%s' "${fact_key}" | sed "s/'/''/g")';")"

  if [ -n "${existing}" ]; then
    record_fact_diff "${run_id}" "${host_key}" "${fact_key}" "" "${fact_value}"
    return 0
  fi

  sqlite3 "${FACTS_DB}" \
    "INSERT OR REPLACE INTO fact_snapshots (inventory_uuid, fact_key, fact_value, collected_at)
     VALUES ('$(printf '%s' "${host_key}" | sed "s/'/''/g")', '$(printf '%s' "${fact_key}" | sed "s/'/''/g")',
             '$(printf '%s' "${fact_value}" | sed "s/'/''/g")', '$(printf '%s' "${collected_at}" | sed "s/'/''/g")');"

  record_fact_diff "${run_id}" "${host_key}" "${fact_key}" "" "${fact_value}"
}

ingest_jsonl_file() {
  local jsonl="$1"
  local run_id="$2"
  local line_num=0
  while IFS= read -r line || [ -n "${line}" ]; do
    line_num=$((line_num + 1))
    [ -z "${line// }" ] && continue
    local host_key hostname collected_at
    host_key="$(jsonl_record_host_key "${line}")"
    hostname="$(jsonl_record_hostname "${line}")"
    collected_at="$(jsonl_record_collected_at "${line}")"
    while IFS=$'\t' read -r fact_key fact_value; do
      [ -n "${fact_key}" ] || continue
      merge_fact_row "${host_key}" "${hostname}" "${fact_key}" "${fact_value}" "${collected_at}" "${run_id}"
    done < <(jsonl_each_fact "${line}")
    validate_record "${line}" || die "invalid jsonl at line ${line_num}"
  done < "${jsonl}"
  record_source_lines "${run_id}" "$(jsonl_line_count "${jsonl}")"
}
