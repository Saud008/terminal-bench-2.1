#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

set +e
cd /app && /usr/local/cargo/bin/cargo build --release --locked && install -m 0755 /app/target/release/relayctl /app/bin/relayctl && python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_sublock_yard_compile.py \
  /tests/test_sublock_verify_simulation.py \
  /tests/test_sublock_interlock_contract.py \
  /tests/test_sublock_hidden_guards.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
