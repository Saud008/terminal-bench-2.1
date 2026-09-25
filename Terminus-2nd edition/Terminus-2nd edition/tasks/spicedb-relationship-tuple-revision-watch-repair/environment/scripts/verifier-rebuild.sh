#!/usr/bin/env bash
set -euo pipefail
export CGO_ENABLED=0
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
go build -mod=readonly -o /usr/local/bin/relationwatchd ./cmd/relationwatchd
