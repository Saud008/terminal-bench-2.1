#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output/*
rm -f /app/state/staging.json /app/state/committed.json /app/state/commit_record.json /app/state/btree-snapshot.json
mkdir -p /app/output /app/state
