#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:${PATH}"
DIR="$(cd "$(dirname "$0")" && pwd)"

cp "${DIR}/files/policy.go" /app/internal/policy/policy.go
cp "${DIR}/files/ledger.go" /app/internal/ledger/ledger.go
cp "${DIR}/files/encrypt.go" /app/internal/encrypt/encrypt.go

cd /app
go build -mod=readonly -o /usr/local/bin/transit-mock ./cmd/transit-mock
