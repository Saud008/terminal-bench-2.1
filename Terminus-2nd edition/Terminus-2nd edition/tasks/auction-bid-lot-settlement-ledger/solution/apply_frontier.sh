#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR="${ROOT_DIR}/files"

cp "${FILES_DIR}/oracle_award.go" /app/internal/lotverdict/award.go
cp "${FILES_DIR}/oracle_catalog.go" /app/internal/scenarioload/catalog.go
cp "${FILES_DIR}/oracle_invoices.go" /app/internal/settlementemit/invoices.go

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
