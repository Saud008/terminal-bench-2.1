#!/usr/bin/env bash
set -euo pipefail
rm -f /app/output/*.json 2>/dev/null || true
rm -f /app/state/playfield-staging/*.json 2>/dev/null || true
mkdir -p /app/output /app/state/playfield-staging
