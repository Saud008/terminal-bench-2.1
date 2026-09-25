#!/usr/bin/env bash
set -euo pipefail

list_fragments_ordered() {
  local dir="$1"
  find "$dir" -maxdepth 1 -type f -name '*.fragment' -printf '%f\n' | sort -r
}
