#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

# Verifier rebuild contract: go build -mod=readonly -o /usr/local/bin/sarbctl ./cmd/sarbctl runs in conftest before pytest.

set +e
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "/tests/test_outputs.py" \
  "/tests/test_curator_artifacts.py" \
  "/tests/test_scan_ledger.py" \
  "/tests/test_policy_curation.py" \
  "/tests/test_delta_emit.py" \
  "/tests/test_verifier_traps.py" \
  -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
