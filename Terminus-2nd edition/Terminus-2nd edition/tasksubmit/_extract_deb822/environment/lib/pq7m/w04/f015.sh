#!/usr/bin/env bash
set -euo pipefail

graph_digest() {
  local body_json="$1"
  echo "$body_json" | jq -c '{run_id, rows: [.package_rows[] | {package, version}]}' \
    | sha256sum | awk '{print $1}'
}
