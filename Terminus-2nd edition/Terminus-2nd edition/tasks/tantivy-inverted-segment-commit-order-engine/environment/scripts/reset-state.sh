#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output/*
rm -rf /app/data/*
rm -f /app/state/index-catalog.json /app/state/index-snapshot.json /app/state/wal-record.json /app/state/wal-*.marker
mkdir -p /app/output /app/state /app/data
