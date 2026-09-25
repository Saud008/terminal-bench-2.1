#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"
cd /app
go build -mod=readonly -o /usr/local/bin/parquet-pushdown-scan ./cmd/parquet-pushdown-scan
