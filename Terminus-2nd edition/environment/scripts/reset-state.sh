#!/usr/bin/env bash
set -euo pipefail

rm -rf /app/work/spool/spam/* /app/work/spool/virus/* /app/work/released/spam/* /app/work/released/virus/* \
  /app/work/ledger.json /app/work/session-state.json \
  /app/state/spool-manifest.json /app/state/release-staging.json /app/state/release-epoch.json \
  /app/state/prepare-seal.json /app/state/custody-journal.jsonl \
  /app/output/*
mkdir -p /app/work/spool/spam /app/work/spool/virus /app/work/released/spam /app/work/released/virus /app/state /app/output

python3 - <<'PY'
import json
doc = {"next_sequence": 1, "entries": []}
with open("/app/work/ledger.json", "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, sort_keys=True)
    fh.write("\n")
state = {
    "releases_attempted": 0,
    "releases_succeeded": 0,
    "releases_failed": 0,
    "duplicate_skipped": 0,
    "release_log": [],
}
with open("/app/work/session-state.json", "w", encoding="utf-8") as fh:
    json.dump(state, fh, indent=2, sort_keys=True)
    fh.write("\n")
PY
