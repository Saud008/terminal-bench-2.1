#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/s3lc.stage.json /app/output/monthly-cost.json /app/state/scan_generation.txt
mkdir -p /app/state /app/output
