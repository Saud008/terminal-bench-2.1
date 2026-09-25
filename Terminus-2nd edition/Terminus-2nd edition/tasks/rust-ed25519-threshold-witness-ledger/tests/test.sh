#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /app/state /app/output /app/bin
echo 0 > /logs/verifier/reward.txt

cd /app
cargo build --release --locked
cp /app/target/release/twctl /app/bin/twctl

set +e
PYTHON_BIN="${PYTHON_BIN:-/opt/verifier-venv/bin/python}"
if [ ! -x "$PYTHON_BIN" ]; then
  PYTHON_BIN=python3
fi
"$PYTHON_BIN" -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
