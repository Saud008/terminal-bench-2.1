#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/chart-manifest/* /app/work/tempo-ledger/* /app/work/beat-grid-ledger/* /app/work/lane-note-ledger/* /app/output/*
mkdir -p /app/state/chart-manifest /app/work/tempo-ledger /app/work/beat-grid-ledger /app/work/lane-note-ledger /app/output
