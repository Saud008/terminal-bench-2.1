#!/usr/bin/env bash
# Legacy decoy tag flattener — not used by tf-tag-sentinel.
set -euo pipefail

legacy_flatten_tags() {
  jq -c '.tags // {}' "$1"
}
