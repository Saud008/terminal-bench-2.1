#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/bondattest-midstate.json
rm -f /app/output/bond-reconnect-attestation.json
rm -rf /app/state/run /app/state/ledger
mkdir -p /app/state /app/output
