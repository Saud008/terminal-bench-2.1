#!/usr/bin/env bash

MERGE_LEDGER="/app/state/merge-ledger.json"

merge_ledger_reset() {
  printf '{"records":[]}\n' > "${MERGE_LEDGER}"
}

merge_record_write() {
  local tree="$1"
  local status="$2"
  local name eapi
  name="$(jq -r '.name' "${tree}/manifest.json")"
  eapi="$(jq -r '.eapi' "${tree}/manifest.json")"
  if [ ! -f "${MERGE_LEDGER}" ]; then
    merge_ledger_reset
  fi
  local tmp
  tmp="$(mktemp)"
  jq \
    --arg name "${name}" \
    --arg status "${status}" \
    --argjson eapi "${eapi}" \
    '.records += [{"package": $name, "status": $status, "eapi": $eapi}]' \
    "${MERGE_LEDGER}" > "${tmp}"
  mv "${tmp}" "${MERGE_LEDGER}"
}

merge_record_for_package() {
  local name="$1"
  if [ ! -f "${MERGE_LEDGER}" ]; then
    echo ""
    return 0
  fi
  jq -r --arg n "${name}" '.records[] | select(.package == $n) | .status' "${MERGE_LEDGER}" | tail -n 1
}
