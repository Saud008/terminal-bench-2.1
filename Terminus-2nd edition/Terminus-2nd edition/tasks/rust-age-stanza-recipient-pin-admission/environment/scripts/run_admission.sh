#!/bin/bash
set -euo pipefail
POLICY="${1:-/app/environment/fixtures/policy/pins.json}"
CORPUS="${AGE_CORPUS_DIR:-/app/environment/fixtures/corpus}"
mkdir -p /app/state /app/output
/app/environment/bin/agerecv stage-witness --corpus "$CORPUS" --policy "$POLICY" --witness /app/state/age-header-witness.json
/app/environment/bin/agerecv seal-ledger --witness /app/state/age-header-witness.json --policy "$POLICY" --out /app/output/age-admission-ledger.json
