#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp -f "${SOL}/golden_key.go" "${APP}/internal/sequence/key.go"
cp -f "${SOL}/golden_window.go" "${APP}/internal/sequence/window.go"
cp -f "${SOL}/golden_epoch.go" "${APP}/internal/ingest/epoch.go"
cp -f "${SOL}/golden_publish.go" "${APP}/internal/batch/publish.go"
cp -f "${SOL}/golden_counter.go" "${APP}/internal/replay/counter.go"
cp -f "${SOL}/golden_export.go" "${APP}/internal/export/ledger.go"
cp -f "${SOL}/golden_run.go" "${APP}/internal/replay/run.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/pulsar-dedup-replay ./cmd/pulsar-dedup-replay

bash "${APP}/scripts/reset-state.sh"
pulsar-dedup-replay export \
  --scenario /app/fixtures/scenarios/07-merged.json \
  --output /app/output/sequence-ledger-export.json
