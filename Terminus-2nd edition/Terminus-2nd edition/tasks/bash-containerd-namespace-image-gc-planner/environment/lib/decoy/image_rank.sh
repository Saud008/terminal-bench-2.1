#!/usr/bin/env bash
# Decoy: ranks images by size only — not on ctrgc hot path
set -euo pipefail
rank_images_by_size() {
  jq -c 'sort_by(.size) | reverse' "$1"
}
