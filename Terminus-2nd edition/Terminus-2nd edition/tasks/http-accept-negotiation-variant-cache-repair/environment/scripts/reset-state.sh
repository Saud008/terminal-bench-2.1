#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
cp /app/fixtures/catalog.json /app/output/active-catalog.json 2>/dev/null || true
mkdir -p /app/output /app/state
rm -f /app/state/negotiation.snapshot.json
: > /app/output/.reset-marker
