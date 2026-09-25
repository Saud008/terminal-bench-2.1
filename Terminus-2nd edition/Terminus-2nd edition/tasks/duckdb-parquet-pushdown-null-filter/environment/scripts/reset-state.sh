#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output/*
rm -f /app/state/pushdown-plan.json
mkdir -p /app/output /app/state
