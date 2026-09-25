#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

set +e
(cd /app && /usr/local/cargo/bin/cargo build --release --locked && cp /app/target/release/rotrace /app/bin/rotrace); python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_brine_chronicle_contract.py \
  /tests/test_ro_pressure_snapshots.py \
  /tests/test_membrane_ndp_lattice.py \
  /tests/test_tb3_ro_train_traps.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
