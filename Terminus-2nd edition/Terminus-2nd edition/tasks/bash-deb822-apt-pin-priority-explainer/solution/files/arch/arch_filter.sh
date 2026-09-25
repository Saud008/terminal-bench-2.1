#!/usr/bin/env bash
set -euo pipefail

arch_ok() {
  local cand_arch="$1"
  local target="$2"
  [[ -n "$cand_arch" ]] || return 1
  [[ "$cand_arch" == "all" || "$cand_arch" == "$target" ]]
}
