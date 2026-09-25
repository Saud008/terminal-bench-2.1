#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/state/manifest-latch/* /app/work/timeline-ledger/* /app/work/sync-lattice/* /app/output/*
mkdir -p /app/state/manifest-latch /app/work/timeline-ledger /app/work/sync-lattice /app/output
