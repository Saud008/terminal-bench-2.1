#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

# cargo build — session conftest rebuilds rtbalctl from /app sources before pytest

set +e
python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_rtbal_compile.py \
  /tests/test_rtbal_accept.py \
  /tests/test_rtbal_balance.py \
  /tests/test_rtbal_closure.py \
  /tests/test_rtbal_hidden.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
