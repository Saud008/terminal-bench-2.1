#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/state/indexes /app/state/tb3-indexes
mkdir -p /app/state/indexes /app/state/tb3-indexes
rm -f /app/state/batch-snapshot.json
rm -rf /app/output/*
