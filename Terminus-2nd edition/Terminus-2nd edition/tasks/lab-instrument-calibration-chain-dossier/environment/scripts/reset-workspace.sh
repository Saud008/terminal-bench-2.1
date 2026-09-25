#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/intake-vault.json
rm -f /app/work/calibration-register.db
rm -rf /app/output/*
mkdir -p /app/state /app/work /app/output
