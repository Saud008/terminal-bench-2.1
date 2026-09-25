#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/ttalloc ./cmd/ttalloc
chmod +x /app/bin/ttalloc
