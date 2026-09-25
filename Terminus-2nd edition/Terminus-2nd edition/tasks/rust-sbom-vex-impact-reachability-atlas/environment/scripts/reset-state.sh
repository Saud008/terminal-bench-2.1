#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/waiver-snapshot.json /app/state/run-seq.json
rm -f /app/output/exposure-ledger.json
echo '{"run_seq":0,"last_fingerprint":""}' > /app/state/run-seq.json
