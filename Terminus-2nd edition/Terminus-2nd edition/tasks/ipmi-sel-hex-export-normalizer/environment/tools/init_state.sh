#!/usr/bin/env bash
# Prepare empty state directories for sel-chain smoke tests.
set -euo pipefail

mkdir -p /app/state /app/output
rm -f /app/state/sel.db /app/state/sel.stage
echo "initialized /app/state and /app/output"
