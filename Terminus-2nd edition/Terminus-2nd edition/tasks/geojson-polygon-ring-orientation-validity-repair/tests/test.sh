#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export VERIFIER_SEED="${VERIFIER_SEED:-geojson-ring-repair-v1}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

set +e
bash /app/scripts/verifier-rebuild.sh
REBUILD_RC=$?

/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
PYTEST_RC=$?

touch /logs/verifier/reward.txt /logs/verifier/ctrf.json 2>/dev/null || true

[ "$REBUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
