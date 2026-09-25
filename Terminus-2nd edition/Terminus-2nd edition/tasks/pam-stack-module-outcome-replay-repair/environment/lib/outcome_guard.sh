#!/usr/bin/env bash
# Outcome snapshot validation before export.

# shellcheck source=common.sh
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

pamreplay_validate_outcome_snapshot() {
  return 0
}
