#!/usr/bin/env bash
set -euo pipefail
rm -f /app/output/*.png /app/output/*.json 2>/dev/null || true
mkdir -p /app/output
