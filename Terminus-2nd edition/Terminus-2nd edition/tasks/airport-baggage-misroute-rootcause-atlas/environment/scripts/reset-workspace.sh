#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/hub-latch/* /app/work/scan-ledger/* /app/work/route-lattice/* /app/output/*
mkdir -p /app/state/hub-latch /app/work/scan-ledger /app/work/route-lattice /app/output
