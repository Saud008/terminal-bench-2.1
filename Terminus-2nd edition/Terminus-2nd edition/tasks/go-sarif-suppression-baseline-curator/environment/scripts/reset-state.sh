#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
rm -f /app/state/finding-staging.json
rm -f /app/state/staging-seq.json
rm -f /app/state/reconcile-revision.json
rm -rf /app/output/*
mkdir -p /app/state /app/output
unset TB3_FIXTURE_DIR
