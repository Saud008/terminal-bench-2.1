#!/usr/bin/env bash
set -euo pipefail
/app/environment/scripts/build_all.sh
mkdir -p /app/state /app/output
/app/environment/bin/wbleguard catalog-bundles \
  --bundles-dir /app/environment/fixtures/bundles \
  --staging /app/state/exchange_attestation.jsonl
/app/environment/bin/wbleguard emit-attestation \
  --staging /app/state/exchange_attestation.jsonl \
  --out /app/output/bundle_attestation_report.json
