#!/usr/bin/env bash
# Retention bucket evaluation (decoy — not used by export hot path).
set -euo pipefail

legacy_prune_estimate() {
  local count="${1:-0}"
  echo $((count * 4096))
}
