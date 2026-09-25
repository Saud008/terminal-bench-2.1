#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp -f "${SOL}/golden_ref.go" "${APP}/internal/deref/ref.go"
cp -f "${SOL}/golden_cycle.go" "${APP}/internal/deref/cycle.go"
cp -f "${SOL}/golden_merge.go" "${APP}/internal/deref/merge.go"
cp -f "${SOL}/golden_nullable.go" "${APP}/internal/deref/nullable.go"
cp -f "${SOL}/golden_discriminator.go" "${APP}/internal/deref/discriminator.go"
cp -f "${SOL}/golden_defaults.go" "${APP}/internal/deref/defaults.go"
cp -f "${SOL}/golden_resolve.go" "${APP}/internal/deref/resolve.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/oasctl ./cmd/oasctl

oasctl validate \
  --spec /app/fixtures/openapi.yaml \
  --payload /app/fixtures/payloads \
  --config /app/config/oasctl.json \
  --output /app/output/validation-report.json
