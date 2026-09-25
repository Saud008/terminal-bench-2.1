#!/usr/bin/env bash
set -euo pipefail
# Decoy helper — not used by compile-stage or emit-manifest hot path.
sort_symbols_alpha() {
  echo "$1" | jq -r 'keys[]' | sort
}
