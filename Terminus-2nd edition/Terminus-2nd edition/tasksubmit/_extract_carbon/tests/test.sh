#!/usr/bin/env bash
set -uo pipefail

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

set +e
bash /app/scripts/rebuild-shift-pl.sh && bash /app/scripts/reset-state.sh && /opt/verifier-venv/bin/pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_shift_hidden_suite.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
