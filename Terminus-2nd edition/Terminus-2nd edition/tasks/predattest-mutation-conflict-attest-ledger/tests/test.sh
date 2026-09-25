#!/usr/bin/env bash
set -uo pipefail

export PATH="/app/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export PYTHONPATH="/app/lib"
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

cd /app || exit 1
TEST_DIR="${TEST_DIR:-/tests}"

# Verifier-only assets (reference math, pinned config, hidden waves) live under
# /tests and must not be agent-readable via /opt. Lock the mount down for the
# verifier process tree.
chmod 700 "${TEST_DIR}" 2>/dev/null || true
chmod 600 \
  "${TEST_DIR}/wavehold_math.py" \
  "${TEST_DIR}/pinned_wavehold.json" \
  "${TEST_DIR}/hidden_waves/"*.jsonl \
  2>/dev/null || true

# /app/scripts/rebuild-wavehold.sh runs from tests/conftest.py session autouse
# (re-links the CLI + refreshes gate bytecode) before pytest collects.

set +e
/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" \
  "${TEST_DIR}/test_wavehold_trap_and_pins.py" \
  -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
