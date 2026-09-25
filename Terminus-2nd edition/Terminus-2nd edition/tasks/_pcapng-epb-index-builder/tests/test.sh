#!/bin/bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
echo '{"version":"1.0.0","results":{"tool":{"name":"pytest"},"summary":{"tests":0,"passed":0,"failed":0,"pending":0,"skipped":0,"other":0,"start":0,"stop":0},"tests":[]}}' > /logs/verifier/ctrf.json

cd /app || { echo 0 > /logs/verifier/reward.txt; exit 1; }

if [ ! -x /app/bin/pcap-index ]; then
  if [ -f /app/Cargo.toml ]; then
    export CARGO_INCREMENTAL=0
    /usr/local/cargo/bin/cargo build --release --locked
    mkdir -p /app/bin
    cp /app/target/release/pcap-index /app/bin/pcap-index
  fi
fi

if [ ! -x /app/bin/pcap-index ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

TEST_DIR="${TEST_DIR:-/tests}"
export PYTHONPATH="${TEST_DIR}:${PYTHONPATH:-}"
export TB3_TS_OFFSET="${TB3_TS_OFFSET:-424242}"

if [ -f "${TEST_DIR}/gen_fixtures.py" ]; then
  /opt/verifier-venv/bin/python "${TEST_DIR}/gen_fixtures.py" 2>/dev/null || true
fi

set +e
/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" -rA
rc=$?
if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
