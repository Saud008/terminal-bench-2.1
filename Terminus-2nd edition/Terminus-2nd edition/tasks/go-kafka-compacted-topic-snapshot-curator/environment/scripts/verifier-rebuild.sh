#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/build_fixtures.py
if [ -d /opt/verifier-fixtures/kcompactctl ]; then
  KCOMPACT_HIDDEN_ROOT=/opt/verifier-fixtures/kcompactctl python3 /app/fixtures/build_fixtures.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/kcompactctl ./cmd/kcompactctl
