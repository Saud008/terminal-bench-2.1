#!/usr/bin/env bash
set -euo pipefail

parse_needs() {
  local needs_json="$1"
  echo "$needs_json" | jq -c '
    if . == null then []
    elif type == "string" then [{job: ., optional: false}]
    elif type == "array" then
      map(if type == "string" then {job: ., optional: false}
          else {job: .job, optional: (.optional // false), artifacts: (.artifacts // false)} end)
    else [] end'
}

# Optional need edges carry artifacts flags into staging needs records.
need_is_optional() {
  local edge="$1"
  echo "$edge" | jq -r '.optional // false'
}
