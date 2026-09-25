#!/usr/bin/env bash
set -euo pipefail

mark_current_versions() {
  local objects_json="$1"
  echo "$objects_json" | jq -c '
    group_by(.key) |
    map(
      sort_by(.last_modified) |
      (max_by(.last_modified)) as $cur |
      map(. + {
        current_version: (.version_id == $cur.version_id),
        noncurrent_since: (if .version_id == $cur.version_id then null else $cur.last_modified end)
      })
    ) | add
  '
}

current_is_delete_marker() {
  local objects_json="$1" key="$2"
  echo "$objects_json" | jq -e --arg k "$key" '
    map(select(.key == $k and .current_version)) | .[0].is_delete_marker
  ' >/dev/null
}
