#!/usr/bin/env bash
set -euo pipefail
pkill -x paramgate 2>/dev/null || true
sleep 0.2
mkdir -p /app/output /app/state
: > /app/output/.keep
rm -f /app/state/bind-snapshot.json
