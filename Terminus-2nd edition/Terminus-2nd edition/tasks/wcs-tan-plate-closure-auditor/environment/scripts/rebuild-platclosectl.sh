#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
mkdir -p /app/bin
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/platclosectl ./cmd/platclosectl
test -x /app/bin/platclosectl
