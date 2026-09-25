#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output /app/state/collectd-ingest.snapshot.json 2>/dev/null || true
mkdir -p /app/output /app/state
