#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

TEST_DIR="${TEST_DIR:-/tests}"
mkdir -p /opt/verifier-fixtures/packages
if [ -d "${TEST_DIR}/verifier-fixtures/packages" ]; then
  cp -a "${TEST_DIR}/verifier-fixtures/packages/." /opt/verifier-fixtures/packages/
fi
export TB3_PACKAGE_ROOT="/opt/verifier-fixtures/packages"

/app/scripts/reset-state.sh

set +e
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
