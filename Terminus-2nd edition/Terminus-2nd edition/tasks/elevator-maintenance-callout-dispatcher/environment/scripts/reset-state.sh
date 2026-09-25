#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state /app/work /app/output
mkdir -p /app/state /app/work /app/output
echo '{"callout_pass":0,"publish_pass":0}' > /app/state/callout-pass.json
