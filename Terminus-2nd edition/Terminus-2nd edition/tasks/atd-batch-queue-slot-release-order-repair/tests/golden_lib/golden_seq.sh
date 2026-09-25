#!/usr/bin/env bash

read_seq() {
  if [[ ! -f "${SEQ_FILE}" ]]; then
    echo "1"
    return 0
  fi
  tr -d '\n\r' < "${SEQ_FILE}"
}

bump_seq() {
  local current="$1"
  local next=$((current + 1))
  local tmp="${SEQ_FILE}.tmp.$$"
  printf '%s\n' "$next" > "${tmp}"
  mv -f "${tmp}" "${SEQ_FILE}"
}
