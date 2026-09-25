#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output /app/state
mkdir -p /app/output /app/state
: > /app/state/broker-ledger.json
echo '{"acked_max":{}}' > /app/state/broker-ledger.json
