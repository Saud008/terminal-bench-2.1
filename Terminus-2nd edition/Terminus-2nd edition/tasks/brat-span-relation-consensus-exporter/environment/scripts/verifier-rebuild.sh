#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/bratctl ./cmd/bratctl
