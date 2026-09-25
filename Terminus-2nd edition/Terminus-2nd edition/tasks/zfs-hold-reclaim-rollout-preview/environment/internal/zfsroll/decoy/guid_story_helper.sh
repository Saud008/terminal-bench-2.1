#!/usr/bin/env bash
# Decoy module not on the load, compile, or publish hot path.
guid_story_helper() {
  local seed="$1"
  echo -n "$seed" | sha256sum | awk '{print $1}'
}
