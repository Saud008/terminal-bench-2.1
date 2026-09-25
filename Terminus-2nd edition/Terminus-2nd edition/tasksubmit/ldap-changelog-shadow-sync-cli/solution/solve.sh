#!/bin/bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"

PATCH_DIR="$(cd "$(dirname "$0")/patches" && pwd)"
cd /app

cp "${PATCH_DIR}/normalize.go" internal/dn/normalize.go
cp "${PATCH_DIR}/apply.go" internal/staging/apply.go
cp "${PATCH_DIR}/usn.go" internal/replay/usn.go
cp "${PATCH_DIR}/ingest.go" internal/ingest/run.go
cp "${PATCH_DIR}/export.go" internal/export/run.go

CGO_ENABLED=0 go build -mod=readonly -o /app/bin/shadow-sync ./cmd/shadow-sync
