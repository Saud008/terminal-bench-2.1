#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output /app/state
mkdir -p /app/output /app/state
rm -f /app/state/archectl-migrate-snapshot.json
rm -f /app/state/archectl-replay-ledger.json
