#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=0

cd /app
go build -trimpath -ldflags="-s -w" -o /usr/local/bin/jktadmit ./cmd/jktadmit
cp /usr/local/bin/jktadmit /app/bin/jktadmit
