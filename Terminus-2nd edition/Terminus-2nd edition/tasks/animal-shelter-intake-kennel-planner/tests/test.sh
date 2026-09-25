#!/usr/bin/env bash
set -euo pipefail
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi
# rebuild-gate: compiled Go intakectl must refresh before pytest
set +e
bash /app/scripts/verifier-rebuild.sh && /opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_kennel_intake_matrix.py \
  /tests/test_kennel_staging_gates.py \
  /tests/test_kennel_tb3_traps.py \
  /tests/test_outputs.py -rA
rc=$?
if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
