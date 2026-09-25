#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
rm -f /app/data/oidguard.db
rm -rf /app/state
mkdir -p /app/data /app/output /app/work /app/work/jsonl-resume /app/state
: > /app/output/.reset-marker
