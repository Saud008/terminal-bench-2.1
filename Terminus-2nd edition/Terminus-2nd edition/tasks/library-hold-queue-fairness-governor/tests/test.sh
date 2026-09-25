#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /opt/verifier-fixtures
if [ -d "${TEST_DIR}/verifier-fixtures" ]; then
  cp -a "${TEST_DIR}/verifier-fixtures/." /opt/verifier-fixtures/
fi
python3 "${TEST_DIR}/build_hidden_scenarios.py"

# Compiled stack contract: go build refresh via verifier-rebuild.sh before pytest.
set +e
bash /app/scripts/verifier-rebuild.sh && /opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "/tests/test_outputs.py" \
  "/tests/test_suspension_priority_contract.py" \
  "/tests/test_pickup_branch_contract.py" \
  "/tests/test_verifier_overlay_traps.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
