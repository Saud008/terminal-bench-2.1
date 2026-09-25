#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
go build -mod=readonly -o /usr/local/bin/wireclock ./cmd/wireclock
bash /app/tooling/reset-state.sh
