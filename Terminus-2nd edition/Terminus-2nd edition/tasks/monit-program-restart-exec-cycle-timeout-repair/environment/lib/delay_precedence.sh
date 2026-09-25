#!/usr/bin/env bash

# Effective start delay after boot events.
monit_effective_start_delay() {
  local onreboot_boot="${1:-0}"
  local start_delay="${2:-0}"
  echo "${start_delay}"
}
