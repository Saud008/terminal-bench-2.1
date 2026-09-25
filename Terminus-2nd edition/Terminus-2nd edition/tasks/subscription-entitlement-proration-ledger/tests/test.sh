#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

# Compiled stack contract: go build refresh via verifier-rebuild.sh before pytest.
set +e
bash /app/scripts/verifier-rebuild.sh && /opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "/tests/test_outputs.py" \
  "/tests/test_proration_scenarios.py" \
  "/tests/test_state_artifacts.py" \
  "/tests/test_verifier_cycles.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
