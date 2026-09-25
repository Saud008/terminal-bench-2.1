#!/usr/bin/env bash
# Decoy — not used by build-policy or candidate-report.
release_label_sort() {
  echo "$1" | jq 'sort_by(.label)'
}
