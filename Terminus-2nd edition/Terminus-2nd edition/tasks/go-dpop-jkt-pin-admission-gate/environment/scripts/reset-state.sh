#!/usr/bin/env bash
set -euo pipefail

rm -f /app/output/deny-ledger.json
rm -f /app/state/chainhead.json
mkdir -p /app/output /app/state /app/work
