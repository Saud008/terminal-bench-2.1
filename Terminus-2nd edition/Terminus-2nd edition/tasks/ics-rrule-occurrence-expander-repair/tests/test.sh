#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export PYTHONDONTWRITEBYTECODE=1
TEST_DIR="${TEST_DIR:-/tests}"
RUN_TESTS="/tmp/ics-verifier-tests"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

rm -rf "${RUN_TESTS}"
mkdir -p "${RUN_TESTS}"
cp "${TEST_DIR}/test_outputs.py" "${RUN_TESTS}/"
cp -r "${TEST_DIR}/verifier-lib" "${RUN_TESTS}/verifier-lib"

set +e
go build -mod=readonly -o /usr/local/bin/expand ./cmd/expand
REBUILD_RC=$?
if [ "$REBUILD_RC" -ne 0 ]; then
  /app/scripts/verifier-rebuild.sh
  REBUILD_RC=$?
fi
/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${RUN_TESTS}/test_outputs.py" -rA
PYTEST_RC=$?

touch /logs/verifier/reward.txt /logs/verifier/ctrf.json 2>/dev/null || true

[ "$REBUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
