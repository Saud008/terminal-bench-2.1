#!/bin/bash
set -euo pipefail

PATCH_DIR="$(cd "$(dirname "$0")/patches" && pwd)"
cd /app

cp "${PATCH_DIR}/parse.go" internal/nmea/parse.go
cp "${PATCH_DIR}/store.go" internal/db/store.go
cp "${PATCH_DIR}/snapshot.go" internal/staging/snapshot.go
cp "${PATCH_DIR}/export.go" internal/export/export.go
cp "${PATCH_DIR}/ingest.go" internal/ingest/ingest.go
cp "${PATCH_DIR}/overlap.go" internal/overlap/calc.go

CGO_ENABLED=0 go build -o /app/bin/tug-berth ./cmd/tug-berth

mkdir -p /app/state /app/output

/app/bin/tug-berth ingest --input /app/fixtures/events_alpha.jsonl --db /app/state/berth.db
/app/bin/tug-berth export --db /app/state/berth.db --out /app/output/berth-report.json
