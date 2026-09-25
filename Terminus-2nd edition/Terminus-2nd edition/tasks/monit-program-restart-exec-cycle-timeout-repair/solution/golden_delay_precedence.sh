#!/usr/bin/env bash

monit_effective_start_delay() {
  local onreboot_boot="${1:-0}"
  local start_delay="${2:-0}"
  if [[ "${onreboot_boot}" == "1" ]]; then
    echo 0
  else
    echo "${start_delay}"
  fi
}
