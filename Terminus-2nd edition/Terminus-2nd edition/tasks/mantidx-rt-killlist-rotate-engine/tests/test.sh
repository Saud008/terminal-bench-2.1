#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

TEST_DIR="${TEST_DIR:-/tests}"

HIDDEN_STAGE="/tmp/mantidx-hidden-$$"
mkdir -p "${HIDDEN_STAGE}"
if [ -d "${TEST_DIR}/data/hidden" ]; then
  cp -a "${TEST_DIR}/data/hidden/." "${HIDDEN_STAGE}/"
fi
export MANTIDX_HIDDEN_DOCS="${HIDDEN_STAGE}"

if ! cargo build --offline --locked --release --bin mantidx; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi
install -m 0755 target/release/mantidx /usr/local/bin/mantidx

set +e
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
