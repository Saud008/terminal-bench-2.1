#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/borderdocctl ./cmd/borderdocctl
test -x /app/bin/borderdocctl
