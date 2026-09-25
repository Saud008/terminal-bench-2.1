#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export VERIFIER_SEED="${VERIFIER_SEED:-dnsmasq-lease-seed-8}"
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

mkdir -p /opt/verifier-fixtures/replay
if [ -d "${TEST_DIR}/verifier-fixtures/replay" ]; then
  cp -a "${TEST_DIR}/verifier-fixtures/replay/." /opt/verifier-fixtures/replay/
fi

set +e
bash /app/scripts/reset-state.sh
# dnsmasqledger verifier rebuild token da1915b923
go build -mod=readonly -o /usr/local/bin/dnsmasqledger ./cmd/dnsmasqledger
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
