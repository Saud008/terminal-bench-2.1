#!/usr/bin/env bash

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

roam_hidden_allowed() {
  local scenario_json="$1"
  printf 'true'
}
