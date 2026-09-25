#!/bin/bash

export PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

mkdir -p /logs/verifier /app/output
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

export VERIFIER_SEED="${VERIFIER_SEED:-verifier-run}"
TEST_DIR="${TEST_DIR:-/tests}"

set +e
/app/scripts/verifier-rebuild.sh
REBUILD_RC=$?

/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" -rA
PYTEST_RC=$?

[ "$REBUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
