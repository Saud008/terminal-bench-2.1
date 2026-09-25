#!/usr/bin/env bash
set -euo pipefail

cd /app
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export GOCACHE="${GOCACHE:-/opt/gocache}"
export GOFLAGS="${GOFLAGS:--mod=readonly}"

go build -mod=readonly -o /usr/local/bin/cdcctl ./cmd/cdcctl
bash /app/scripts/reset-state.sh
