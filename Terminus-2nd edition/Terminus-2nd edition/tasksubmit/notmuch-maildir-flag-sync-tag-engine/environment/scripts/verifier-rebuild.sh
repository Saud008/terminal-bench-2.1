#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=1
export GOFLAGS="-mod=readonly"
export GOCACHE="${GOCACHE:-/opt/gocache}"

cd /app
go build -mod=readonly -o /usr/local/bin/mailsync ./cmd/mailsync
test -x /usr/local/bin/mailsync
