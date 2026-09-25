#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/work/scripts /app/work/registry /app/work/state.json
mkdir -p /app/work/scripts /app/work/registry /app/var/spool/at/jobs /app/var/spool/at/batch_slots /app/output
rm -f /app/var/spool/at/jobs/* /app/var/spool/at/batch_slots/* 2>/dev/null || true
echo "1" > /app/var/spool/at/.SEQ

echo "at replay work state reset"
