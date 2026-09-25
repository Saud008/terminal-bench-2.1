#!/usr/bin/env bash
set -euo pipefail

rm -f /app/state/grant-portfolio.db
mkdir -p /app/state /app/output
echo '{"amendment_pass":0}' > /app/state/amendment-pass.json
rm -f /app/output/spend-atlas.json
