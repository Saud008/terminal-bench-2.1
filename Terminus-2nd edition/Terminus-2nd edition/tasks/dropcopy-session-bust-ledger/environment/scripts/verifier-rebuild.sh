#!/usr/bin/env bash
set -euo pipefail
cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/dropcopyctl ./cmd/dropcopyctl
