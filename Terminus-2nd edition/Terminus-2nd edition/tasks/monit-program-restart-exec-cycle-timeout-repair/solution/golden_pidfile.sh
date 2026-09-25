#!/usr/bin/env bash

monit_prepare_pidfile() {
  local pidfile="$1"
  local unclean="${2:-0}"
  mkdir -p "$(dirname "${pidfile}")"
  if [[ "${unclean}" == "1" && -f "${pidfile}" ]]; then
    rm -f "${pidfile}"
    echo 0
    return 0
  fi
  if [[ -f "${pidfile}" ]]; then
    echo 0
    return 0
  fi
  echo 0
}

monit_write_pidfile() {
  local pidfile="$1"
  local token="$2"
  mkdir -p "$(dirname "${pidfile}")"
  printf '%s\n' "${token}" > "${pidfile}"
}

monit_clear_pidfile() {
  local pidfile="$1"
  rm -f "${pidfile}"
}
