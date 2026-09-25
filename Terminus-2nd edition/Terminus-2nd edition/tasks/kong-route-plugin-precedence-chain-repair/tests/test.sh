#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

TEST_DIR="${TEST_DIR:-/tests}"
for f in "${TEST_DIR}/test.sh" "${TEST_DIR}/"*.py; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
  fi
done

bash /app/scripts/reset-state.sh

set +e
bash /app/scripts/verifier-rebuild.sh
REBUILD_RC=$?

/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" \
  "${TEST_DIR}/test_m1.py" "${TEST_DIR}/test_m2.py" "${TEST_DIR}/test_m3.py" -rA
PYTEST_RC=$?

[ "$REBUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
