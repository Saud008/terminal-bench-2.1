#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"
export GOCACHE="${GOCACHE:-/home/agent/.cache/go-build}"
mkdir -p "${GOCACHE}"
cd /app
python3 /app/fixtures/build_fixtures.py
# Hidden fixtures are root-owned read-only; image build already materialized them.
if [ -d /opt/verifier-fixtures/iceexpctl ] && [ -w /opt/verifier-fixtures/iceexpctl ]; then
  ICEEXP_HIDDEN_ROOT=/opt/verifier-fixtures/iceexpctl python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/iceexpctl ./cmd/iceexpctl
