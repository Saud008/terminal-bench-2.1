#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /opt/verifier-fixtures
if [ -d "${TEST_DIR}/verifier-fixtures" ]; then
  cp -a "${TEST_DIR}/verifier-fixtures/." /opt/verifier-fixtures/
fi

bash /app/scripts/reset-state.sh || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

set +e
go build -mod=readonly -o /usr/local/bin/zeebe-bpmn-replay ./cmd/zeebe-bpmn-replay
REBUILD_RC=$?

/opt/verifier-venv/bin/python -m pytest -rA -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py"
PYTEST_RC=$?

[ "$REBUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
