#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:${PATH}"
cd /app
python3 /app/fixtures/gen_degree_db.py
if [ -d /opt/verifier-fixtures/degaudit ]; then
  DEGAUDIT_HIDDEN_ROOT=/opt/verifier-fixtures/degaudit python3 /app/fixtures/gen_degree_db.py
fi
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/degaudit ./cmd/degaudit
