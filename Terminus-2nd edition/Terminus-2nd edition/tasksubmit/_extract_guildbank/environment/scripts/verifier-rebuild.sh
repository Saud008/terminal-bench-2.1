#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=0

cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/guildbankd ./cmd/guildbankd
