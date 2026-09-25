#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
  exit 1
fi

PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /opt/verifier-fixtures/wireclock
cp "${TEST_DIR}/patches/"*.go /opt/verifier-fixtures/wireclock/
export TB3_FIXTURE_DIR=/opt/verifier-fixtures/wireclock

bash /app/tooling/reset-state.sh
cd /app && go build -mod=readonly -o /usr/local/bin/wireclock ./cmd/wireclock

/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
