#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

rm -f /app/state/event-staging.json
rm -f /app/state/staging-seq.json
rm -f /app/state/correlate-generation.json
rm -rf /app/output/*
mkdir -p /app/state /app/output

unset YARACOR_FIXTURE_DIR
