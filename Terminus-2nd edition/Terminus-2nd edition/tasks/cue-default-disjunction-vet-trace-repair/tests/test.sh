#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export PYTHONDONTWRITEBYTECODE=1
TEST_DIR="${TEST_DIR:-/tests}"
RUN_TESTS="/tmp/cue-verifier-tests"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

rm -rf "${RUN_TESTS}"
mkdir -p "${RUN_TESTS}"
cp "${TEST_DIR}/test_outputs.py" "${RUN_TESTS}/"
cp -r "${TEST_DIR}/verifier-lib" "${RUN_TESTS}/verifier-lib"
cp -r "${TEST_DIR}/verifier-golden" "${RUN_TESTS}/verifier-golden"

set +e
bash /app/scripts/verifier-rebuild.sh
REBUILD_RC=$?
go build -o /usr/local/bin/cuectl ./cmd/cuectl
REBUILD_RC=$((REBUILD_RC + $?))
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${RUN_TESTS}/test_outputs.py" -rA
PYTEST_RC=$?

touch /logs/verifier/reward.txt /logs/verifier/ctrf.json 2>/dev/null || true

[ "$REBUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
