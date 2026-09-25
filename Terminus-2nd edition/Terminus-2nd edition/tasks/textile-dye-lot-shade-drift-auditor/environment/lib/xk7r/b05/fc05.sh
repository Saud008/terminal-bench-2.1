#!/usr/bin/env bash
set -euo pipefail

in_rework_window() {
  local measured="$1"
  local start="$2"
  local end="$3"
  if (( measured >= start && measured < end )); then
    echo "yes"
  else
    echo "no"
  fi
}
