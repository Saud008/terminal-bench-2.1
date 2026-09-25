#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/* /app/work/* /app/output/*
mkdir -p /app/state /app/work /app/output
echo '{"apq_audit_seq":0}' > /app/state/apq-audit-seq.json
