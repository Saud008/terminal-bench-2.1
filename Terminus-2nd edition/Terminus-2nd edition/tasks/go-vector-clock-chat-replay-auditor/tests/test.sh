#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

# rebuild-in-test: conftest session fixture runs /app/scripts/verifier-rebuild.sh
# Use the venv console-script (not `python -m pytest`) so /app is not on sys.path
# and an agent-planted /app/pytest.py cannot short-circuit reward=1.

set +e
cd /tests
/opt/verifier-venv/bin/pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "/tests/test_outputs.py" \
  "/tests/test_vecchat_shard_load.py" \
  "/tests/test_vecchat_reconcile_gates.py" \
  "/tests/test_vecchat_timeline_seal.py" \
  "/tests/test_vecchat_tb3_traps.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
