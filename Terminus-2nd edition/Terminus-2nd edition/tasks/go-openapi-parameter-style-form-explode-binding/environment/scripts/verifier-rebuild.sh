#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
go build -mod=readonly -o /tmp/paramgate ./cmd/paramgate
install -m 0755 /tmp/paramgate /usr/local/bin/paramgate
