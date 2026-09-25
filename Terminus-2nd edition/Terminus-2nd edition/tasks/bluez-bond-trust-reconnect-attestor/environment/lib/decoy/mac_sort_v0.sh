#!/usr/bin/env bash
set -euo pipefail

sort_macs_v0() {
  local input="$1"
  echo "$input" | tr ':' '\n' | sort
}
