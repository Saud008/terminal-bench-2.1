#!/usr/bin/env bash
# Decoy — not used by ingest or export hot path.
mesh_rank_helper() {
  echo "$1" | jq 'sort_by(.metric) | reverse'
}
