#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/* /app/work/* /app/output/*
mkdir -p /app/state /app/work /app/output
echo '{"audit_generation":0}' > /app/state/audit-generation.json
