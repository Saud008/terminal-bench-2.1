#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/pressure-buffer/* /app/work/cleaning-buffer/* /app/work/ndp-grid/* /app/work/trend-scratch/* /app/output/*
mkdir -p /app/state/pressure-buffer /app/work/cleaning-buffer /app/work/ndp-grid /app/work/trend-scratch /app/output
