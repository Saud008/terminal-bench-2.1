#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

tscn_find_orphans() {
  local merged_json="$1"
  echo "[]"
}
