#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output /app/data/ingest
mkdir -p /app/output /app/data/ingest
curl -sf -X POST http://127.0.0.1:9090/api/v1/reset >/dev/null 2>&1 || true
