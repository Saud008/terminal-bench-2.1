#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifie
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

cargo build --release --locked
cp /app/target/release/stationclos /app/bin/stationclos

set +e
python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_hull_ledger_lane.py \
  /tests/test_tb3_geohull_probes.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
