#!/usr/bin/env bash

rf_console_verify() {
  local dump_path="$1"
  local key_epoch="$2"
  local checksum_algo_id="$3"
  local index_db="$4"
  local matched=0
  while IFS= read -r line; do
    [[ -z "${line}" ]] && continue
    local hash_part epoch_part algo_part hash_val
    hash_part="${line#hash=}"
    hash_val="${hash_part%% *}"
    epoch_part="${line#*epoch=}"
    epoch_part="${epoch_part%% *}"
    algo_part="${line#*algo=}"
    algo_part="${algo_part%% *}"
    local found
    found="$(sqlite3 "${index_db}" "SELECT COUNT(*) FROM fuzzy_hashes WHERE hash='${hash_val}' AND key_epoch=${epoch_part} AND checksum_algo_id=${algo_part};")"
    if [[ "${found}" -gt 0 ]]; then
      matched=$((matched + 1))
    else
      return 1
    fi
  done < "${dump_path}"
  echo "${matched}"
}
