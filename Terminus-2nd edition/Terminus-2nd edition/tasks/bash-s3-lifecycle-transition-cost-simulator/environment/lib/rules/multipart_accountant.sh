#!/usr/bin/env bash
set -euo pipefail

is_incomplete_mpu() {
  local row="$1"
  [[ "$(echo "$row" | jq -r '.multipart_complete')" == "false" && "$(echo "$row" | jq -r '.multipart_id')" != "null" ]]
}

dedupe_completed_mpu() {
  local objects_json="$1"
  echo "$objects_json" | jq -c '
    group_by(.multipart_id) |
    map(
      if (.[0].multipart_id != null) and (.[0].multipart_complete == true) then
        [.[0]]
      else . end
    ) | add
  '
}

sum_incomplete_mpu_bytes() {
  local objects_json="$1"
  echo "$objects_json" | jq '[.[] | select(.multipart_complete==false and .multipart_id!=null) | .size_bytes] | add // 0'
}
