#!/usr/bin/env bash
set -euo pipefail

staging_digest() {
  local body_json="$1"
  echo "$body_json" | jq -c '{run_id, jobs: [.jobs[] | {name, stage, active}]}' \
    | sha256sum | awk '{print $1}'
}
