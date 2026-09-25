#!/usr/bin/env bash
# Decoy module not on inventory or preview hot path.
digest_story_helper() {
  local json_blob="$1"
  echo "$json_blob" | sha256sum | awk '{print $1}'
}
