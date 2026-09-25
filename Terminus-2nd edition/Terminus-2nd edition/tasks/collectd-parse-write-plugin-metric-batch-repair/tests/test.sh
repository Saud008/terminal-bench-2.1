#!/usr/bin/env bash
set -uo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export VERIFIER_SEED="${VERIFIER_SEED:-collectd-seed-160}"
TEST_DIR="${TEST_DIR:-/tests}"

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

set +e
go build -mod=readonly -o /usr/local/bin/collectdctl ./cmd/collectdctl
BUILD_RC=$?

/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
PYTEST_RC=$?

touch /logs/verifier/reward.txt /logs/verifier/ctrf.json 2>/dev/null || true

[ "$BUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
