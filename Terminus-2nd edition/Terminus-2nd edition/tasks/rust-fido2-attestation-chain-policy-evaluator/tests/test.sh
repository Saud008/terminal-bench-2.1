#!/usr/bin/env bash
set -euo pipefail

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

set +e
cd /app && /usr/local/cargo/bin/cargo build --release --locked && install -m 0755 /app/target/release/fido2eval /app/bin/fido2eval && python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_attest_contract.py \
  /tests/test_attest_hidden.py \
  /tests/test_attest_guards.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
