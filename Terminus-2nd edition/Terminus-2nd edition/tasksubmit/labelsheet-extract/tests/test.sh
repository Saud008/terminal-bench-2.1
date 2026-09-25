#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/app/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
export PYTHONPATH="/app/lib:${PYTHONPATH:-}"
export SHEET_APP_ROOT="/app"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

set +e
bash /app/scripts/rebuild-sheet.sh
bash /app/scripts/reset-state.sh
RESET_RC=$?
if [ "$RESET_RC" -ne 0 ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
