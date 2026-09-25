#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state /app/work /app/output
mkdir -p /app/state /app/work /app/output
echo '{"adjudication_pass":0,"finalize_pass":0}' > /app/state/adjudication-pass.json
