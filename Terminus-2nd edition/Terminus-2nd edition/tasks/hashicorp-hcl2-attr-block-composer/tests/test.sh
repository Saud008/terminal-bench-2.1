#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /app/state /app/output /app/bin
echo 0 > /logs/verifier/reward.txt

cd /app
export PATH="/usr/local/go/bin:${PATH}"
go build -o /app/bin/hclctl ./cmd/hclctl

set +e
python3 -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
  exit 0
else
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi
