#!/usr/bin/env bash
set -euo pipefail
mkdir -p /app/output /app/fixtures/policies
rm -f /app/output/*
if [ -d /opt/verifier-fixtures/policies ]; then
  find /app/fixtures/policies -mindepth 1 -delete 2>/dev/null || true
  cp -a /opt/verifier-fixtures/policies/. /app/fixtures/policies/
fi
pkill -f '/usr/local/bin/transit-mock' 2>/dev/null || true
sleep 0.2
