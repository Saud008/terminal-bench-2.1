#!/usr/bin/env bash
set -euo pipefail

cpu_arch_allowed() {
  local cand_arch="$1"
  local target="$2"
  # Baseline treats missing arch as universal.
  if [[ -z "$cand_arch" ]]; then
    return 0
  fi
  [[ "$cand_arch" == "all" || "$cand_arch" == "$target" ]]
}
