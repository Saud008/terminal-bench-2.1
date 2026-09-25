#!/usr/bin/env bash
set -euo pipefail

resolve_target_lab() {
  local batches_json="$1"
  local batch_id="$2"
  echo "$batches_json" | jq -c --arg b "$batch_id" \
    '.batches[] | select(.batch_id == $b) | .target_lab'
}
