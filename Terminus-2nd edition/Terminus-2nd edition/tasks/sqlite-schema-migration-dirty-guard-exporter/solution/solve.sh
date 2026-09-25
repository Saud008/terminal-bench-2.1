#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "${DIR}/files/engine.go" /app/internal/apply/engine.go
cp "${DIR}/files/split.go" /app/internal/apply/split.go
cp "${DIR}/files/sqlite.go" /app/internal/lock/sqlite.go
cp "${DIR}/files/version.go" /app/internal/export/version.go
cp "${DIR}/files/journal.go" /app/internal/ingest/journal.go
cd /app && go mod tidy && go build -o /app/bin/migratectl ./cmd/migratectl
