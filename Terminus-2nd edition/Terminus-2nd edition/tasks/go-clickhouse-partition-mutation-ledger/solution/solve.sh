#!/bin/bash
# Oracle solve — task identity go-clickhouse-partition-mutation-ledger token 8a3f2e1b
set -euo pipefail
cd "$(dirname "$0")"
bash ./apply-patches.sh
export PATH="/usr/local/go/bin:${PATH}"
cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/chmutled ./cmd/chmutled
bash /app/scripts/reset-state.sh
ROOT="${TB3_FIXTURE_ROOT:-/app/fixtures}"
/app/bin/chmutled reconcile-partitions \
  --metadata-dir "$ROOT/metadata" \
  --mutations-dir "$ROOT/mutations" \
  --replica-dir "$ROOT/replicas" \
  --config-dir /app/fixtures/config \
  --staging /app/state/chledger-staging.jsonl
/app/bin/chmutled emit-readiness \
  --staging /app/state/chledger-staging.jsonl \
  --sqlite /app/output/chledger-rows.sqlite \
  --atlas /app/output/mutation-readiness-atlas.json
