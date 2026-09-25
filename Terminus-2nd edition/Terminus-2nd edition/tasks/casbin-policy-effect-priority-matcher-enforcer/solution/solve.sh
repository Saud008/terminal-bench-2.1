#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${SOL}/files"

cp -f "${FILES}/golden_load.go" "${APP}/internal/authzkernel/load.go"
cp -f "${FILES}/golden_role.go" "${APP}/internal/authzkernel/role.go"
cp -f "${FILES}/golden_match.go" "${APP}/internal/authzkernel/match.go"
cp -f "${FILES}/golden_effect.go" "${APP}/internal/authzkernel/effect.go"
cp -f "${FILES}/golden_enforce.go" "${APP}/internal/authzkernel/enforce.go"
cp -f "${FILES}/golden_staging.go" "${APP}/internal/authzkernel/staging.go"
cp -f "${FILES}/golden_audit.go" "${APP}/internal/authzkernel/audit.go"

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd "${APP}"
go build -mod=readonly -o /usr/local/bin/casctl ./cmd/casctl

casctl enforce \
  --config /app/config/casctl.json \
  --requests /app/fixtures/requests/batch-alpha.jsonl \
  --output /app/output/enforce-report.json
