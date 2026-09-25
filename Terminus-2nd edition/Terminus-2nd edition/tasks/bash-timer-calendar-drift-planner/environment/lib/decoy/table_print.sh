#!/usr/bin/env bash
# Decoy table printer — not on export hot path.
set -euo pipefail

print_timer_row() {
  local name="$1"
  local mode="$2"
  printf '%-24s %s\n' "${name}" "${mode}"
}
