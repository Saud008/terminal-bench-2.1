#!/usr/bin/env bash
set -euo pipefail

rm -f /app/state/*.json /app/state/*.tsv /app/state/*.cache /app/state/config.hash 2>/dev/null || true
mkdir -p /app/state /app/output /app/tmp
