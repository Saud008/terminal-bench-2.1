#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/trust_ledger.json /app/state/scan_generation.txt
rm -f /app/output/principals_attestation_bundle.json
mkdir -p /app/state /app/output
echo 0 > /app/state/scan_generation.txt
