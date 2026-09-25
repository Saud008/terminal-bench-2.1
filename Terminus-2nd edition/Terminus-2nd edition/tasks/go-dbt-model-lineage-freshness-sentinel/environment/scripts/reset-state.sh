#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/manifest-checkpoint.json /app/work/freshness-scans.db /app/output/*
mkdir -p /app/state /app/work /app/output
