#!/usr/bin/env bash
set -euo pipefail
STATE="/app/state"
rm -f "${STATE}/committed.json" "${STATE}/staging.json" "${STATE}/page_registry.json"
rm -f "${STATE}/split_journal.jsonl" "${STATE}/sled-staging-snapshot.json"
rm -f "${STATE}/commit_record.json" "${STATE}/pages.json" "${STATE}/applied_splits.json"
rm -f "${STATE}/journal_replay_run.json"
rm -rf "${STATE}/pins" "${STATE}/tb3_lane"
mkdir -p "${STATE}/pins" /app/output
