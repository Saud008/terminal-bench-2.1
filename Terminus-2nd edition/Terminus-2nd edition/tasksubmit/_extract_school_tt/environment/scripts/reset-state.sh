#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/* /app/work/* /app/output/*
mkdir -p /app/state /app/work /app/output
echo '{"allocation_pass":0}' > /app/state/allocation-pass.json
