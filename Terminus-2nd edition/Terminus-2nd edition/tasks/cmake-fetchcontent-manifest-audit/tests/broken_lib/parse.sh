#!/usr/bin/env bash
# Parse orchestrator — ingest snapshot then export tree JSON.

# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/ingest.sh"
# shellcheck source=/dev/null
source "$(dirname "${BASH_SOURCE[0]}")/export_tree.sh"

parse_cmake_tree() {
  local root="$1"
  ingest_cmake_tree "$root"
  write_ingest_snapshot
  export_cmake_tree
}
