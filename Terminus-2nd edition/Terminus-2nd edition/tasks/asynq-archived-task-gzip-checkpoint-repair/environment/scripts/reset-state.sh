#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/work /app/state /app/output
mkdir -p /app/work/archives /app/state /app/output
rm -f /app/work/queue.db
