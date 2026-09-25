#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp -f "${SOL}/files/pending.go" "${APP}/internal/ingest/pending.go"
cp -f "${SOL}/files/resolver.go" "${APP}/internal/incident/resolver.go"
cp -f "${SOL}/files/handler.go" "${APP}/internal/boundary/handler.go"
cp -f "${SOL}/files/activator.go" "${APP}/internal/job/activator.go"
cp -f "${SOL}/files/merge.go" "${APP}/internal/variables/merge.go"
cp -f "${SOL}/files/deduper.go" "${APP}/internal/replay/deduper.go"
cp -f "${SOL}/files/report.go" "${APP}/internal/export/report.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/actplay ./cmd/actplay

bash "${APP}/scripts/reset-state.sh"
actplay export \
  --scenario /app/fixtures/scenarios/07-merged.json \
  --output /app/output/job-activation-export.json
