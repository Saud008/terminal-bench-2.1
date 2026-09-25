#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
go build -mod=readonly -o /usr/local/bin/vtgatesim ./cmd/vtgatesim
