#!/bin/bash
# Shared snapshot record helpers.
set -euo pipefail

load_snapshot_records() {
  local snap="$1"
  local -n out_records="$2"
  out_records=()
  local line
  while IFS= read -r line || [[ -n "${line}" ]]; do
    [[ "${line}" == schema_version=* ]] && continue
    [[ "${line}" == catalog_digest=* ]] && continue
    [[ -z "${line}" ]] && continue
    out_records+=("${line}")
  done < "${snap}"
}

record_field() {
  local rec="$1" field="$2"
  if [[ "${field}" == module ]]; then
    echo "${rec#module|}" | cut -d'|' -f1
    return
  fi
  local key="${field}="
  local -a segments=()
  IFS='|' read -ra segments <<< "${rec}"
  local segment
  for segment in "${segments[@]}"; do
    if [[ "${segment}" == "${key}"* ]]; then
      echo "${segment#${key}}"
      return
    fi
  done
  if [[ "${field}" == priority ]]; then
    echo "0"
  else
    echo ""
  fi
}

lookup_record() {
  local name="$1"
  local -n target_recs="$2"
  local r
  for r in "${target_recs[@]}"; do
    [[ "$(record_field "${r}" module)" == "${name}" ]] && { echo "${r}"; return 0; }
  done
  return 1
}
