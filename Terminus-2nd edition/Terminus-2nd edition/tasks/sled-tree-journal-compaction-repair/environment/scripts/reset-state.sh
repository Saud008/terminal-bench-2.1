#!/usr/bin/env bash
set -euo pipefail
rm -rf /app/output/*
rm -f \
  /app/state/staging.json \
  /app/state/committed.json \
  /app/state/commit_record.json \
  /app/state/btree-snapshot.json \
  /app/state/sled-staging-snapshot.json \
  /app/state/page_registry.json \
  /app/state/split_journal.jsonl \
  /app/state/applied_splits.json \
  /app/state/journal_replay_run.json
rm -rf /app/state/pins
mkdir -p /app/output /app/state
