#!/usr/bin/env bash

allocate_letter() {
  local start_letter="$1"
  local seq_val="$2"
  local letter="$start_letter"
  local code
  code="$(printf '%d' "'$letter")"
  if [[ -f "${BATCH_SLOTS}/${letter}" ]]; then
    echo ""
    return 0
  fi
  echo "$letter"
}

letter_spool_exists() {
  local letter="$1"
  local count
  count="$(find "${SPOOL_DIR}" -maxdepth 1 -name "${letter}*" 2>/dev/null | wc -l | tr -d ' ')"
  [[ "$count" != "0" ]]
}
