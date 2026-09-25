#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state /app/work /app/output
mkdir -p /app/state /app/work /app/output
echo '{"screening_pass":0,"seal_pass":0}' > /app/state/screening-pass.json
