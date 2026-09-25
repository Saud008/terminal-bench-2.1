#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ] || [ -z "${PWD:-}" ]; then
  echo "Error: No working directory set." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

mkdir -p /opt/verifier-fixtures
if [ -d "${TEST_DIR}/verifier-fixtures" ]; then
  cp -a "${TEST_DIR}/verifier-fixtures/." /opt/verifier-fixtures/
fi

set +e
bash /app/scripts/reset-state.sh
go build -mod=readonly -o /usr/local/bin/nsecval ./cmd/nsecval
if [ $? -ne 0 ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi
/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
