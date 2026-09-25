#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /opt/verifier-fixtures/termsetctl
if [ -d "${TEST_DIR}/verifier-fixtures/termsetctl" ]; then
  cp -a "${TEST_DIR}/verifier-fixtures/termsetctl/." /opt/verifier-fixtures/termsetctl/
fi

# Compiled stack contract: go build refresh via verifier-rebuild.sh before pytest.
set +e
bash /app/scripts/verifier-rebuild.sh && /opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" \
  "${TEST_DIR}/test_acquirer_fsm_contract.py" \
  "${TEST_DIR}/test_terminal_key_hidden_traps.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
