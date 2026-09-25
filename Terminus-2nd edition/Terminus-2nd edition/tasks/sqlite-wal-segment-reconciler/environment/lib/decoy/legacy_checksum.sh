#!/usr/bin/env bash
# Decoy checksum helper — not used by wal-chain reconcile/stage/export hot path.
set -euo pipefail

legacy_crc32_placeholder() {
  echo "decoy-only"
}
