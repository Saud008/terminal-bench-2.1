#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /app/state /app/output /app/bin
echo 0 > /logs/verifier/reward.txt

cd /app
export PATH="/usr/local/cargo/bin:/app/bin:${PATH}"
cargo build --release
cp /app/target/release/tantictl /app/bin/tantictl

set +e
python3 -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
