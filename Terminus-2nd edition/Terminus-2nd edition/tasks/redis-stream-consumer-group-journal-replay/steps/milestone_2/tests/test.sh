#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /app/state /app/output /app/bin

cd /app
go build -o /app/bin/redisctl ./cmd/redisctl

set +e
python -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_m2.py -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
