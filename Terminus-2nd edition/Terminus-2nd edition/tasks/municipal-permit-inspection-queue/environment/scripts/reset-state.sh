#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/* /app/work/* /app/output/* /app/intermediate/*
mkdir -p /app/state /app/work /app/output /app/intermediate
echo '{"queue_pass":0,"publish_pass":0}' > /app/state/queue-pass.json
rm -f /app/state/permit.db
