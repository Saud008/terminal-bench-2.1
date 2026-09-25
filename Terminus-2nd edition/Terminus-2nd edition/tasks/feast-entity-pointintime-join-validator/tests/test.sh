#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /app/state /app/work /app/output
echo 0 > /logs/verifier/reward.txt

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
cd /app
go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/feastctl ./cmd/feastctl

set +e
/opt/verifier-venv/bin/python -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_outputs.py -rA
rc=$?
if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
