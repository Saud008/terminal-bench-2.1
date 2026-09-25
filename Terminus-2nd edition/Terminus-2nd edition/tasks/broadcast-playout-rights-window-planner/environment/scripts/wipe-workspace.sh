#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/* /app/work/* /app/output/*
mkdir -p /app/state /app/work /app/output
echo '{"plan_pass":0}' > /app/state/compile-epoch.json
