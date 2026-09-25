#!/usr/bin/env bash
# Rebuild gate: validate gawk stage modules before pytest.
set -euo pipefail

for awk in /app/lib/ingest.awk /app/lib/bucket.awk /app/lib/export.awk; do
  gawk -f "${awk}" /dev/null 2>/dev/null || gawk --lint -f "${awk}" /dev/null
done
