#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/tele-buffer/* /app/work/fuel-buffer/* /app/work/probe-grid/* /app/work/balance-scratch/* /app/output/*
mkdir -p /app/state/tele-buffer /app/work/fuel-buffer /app/work/probe-grid /app/work/balance-scratch /app/output
