#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export PYTHONDONTWRITEBYTECODE=1
TEST_DIR="${TEST_DIR:-/tests}"
RUN_TESTS="/tmp/http-accept-verifier-tests"

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
cp "${TEST_DIR}/reference_variantgate.py" "${RUN_TESTS}/"
cp -r "${TEST_DIR}/module_oracles" "${RUN_TESTS}/module_oracles"

set +e
bash /app/scripts/reset-state.sh
RESET_RC=$?
go build -mod=readonly -o /usr/local/bin/variantgate ./cmd/variantgate
BUILD_RC=$?
/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${RUN_TESTS}/test_outputs.py" -rA
PYTEST_RC=$?

touch /logs/verifier/reward.txt /logs/verifier/ctrf.json 2>/dev/null || true

[ "$RESET_RC" -eq 0 ] && [ "$BUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
