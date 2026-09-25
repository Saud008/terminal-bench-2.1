#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export GOFLAGS="-mod=vendor"

cd /app
cp /opt/verifier-broken-radiusproxy/interval.go internal/attribute/interval.go
cp /opt/verifier-broken-radiusproxy/dedupe.go internal/session/dedupe.go
cp /opt/verifier-broken-radiusproxy/queue.go internal/proxy/queue.go
cp /opt/verifier-broken-radiusproxy/sqlite.go internal/store/sqlite.go
cp /opt/verifier-broken-radiusproxy/stage.go internal/export/stage.go
cp /opt/verifier-broken-radiusproxy/rollup.go internal/export/rollup.go
go build -mod=vendor -o /usr/local/bin/radiusproxy ./cmd/radiusproxy
