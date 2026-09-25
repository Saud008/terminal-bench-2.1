#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"
DIR="$(cd "$(dirname "$0")" && pwd)"
cp "${DIR}/patches/parse.go" /app/internal/parse/parse.go
cp "${DIR}/patches/bind.go" /app/internal/bind/bind.go
cp "${DIR}/patches/plan.go" /app/internal/plan/plan.go
cd /app
go build -mod=readonly -o /usr/local/bin/tekton-mount-plan ./cmd/tekton-mount-plan
