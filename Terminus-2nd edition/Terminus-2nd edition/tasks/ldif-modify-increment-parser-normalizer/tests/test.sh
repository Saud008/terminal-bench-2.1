#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set WORKDIR in your Dockerfile before running this script." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /app/crates/ldif-core/tests
cp "${TEST_DIR}/module_contracts.rs" /app/crates/ldif-core/tests/module_contracts.rs

if ! cargo test --locked -p ldif-core; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

if ! cargo build --locked --release --bin ldif-apply; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi
install -m 0755 target/release/ldif-apply /usr/local/bin/ldif-apply

set +e
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
