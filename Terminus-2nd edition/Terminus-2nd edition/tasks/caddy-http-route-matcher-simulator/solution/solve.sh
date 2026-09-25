#!/usr/bin/env bash
set -euo pipefail

ROOT="/solution/files"
cp "$ROOT/internal/matcher/engine.go" /app/internal/matcher/engine.go
cp "$ROOT/internal/matcher/pathregexp.go" /app/internal/matcher/pathregexp.go
cp "$ROOT/internal/matcher/header.go" /app/internal/matcher/header.go
cp "$ROOT/internal/matcher/specificity.go" /app/internal/matcher/specificity.go
cp "$ROOT/internal/export/export.go" /app/internal/export/export.go

cd /app
go build -o /app/bin/caddyctl ./cmd/caddyctl
