#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export PYTHONDONTWRITEBYTECODE=1
export VERIFIER_SEED="${VERIFIER_SEED:-amavis-quarantine-spool-release-ledger}"

TEST_DIR="${TEST_DIR:-/tests}"
RUN_TESTS="/tmp/amavis-verifier-tests"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '%s\n' '{"version":"1.0.0","results":{"tool":{"name":"pytest"},"summary":{"tests":0,"passed":0,"failed":0,"skipped":0},"tests":[]}}' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

rm -rf "${RUN_TESTS}"
mkdir -p "${RUN_TESTS}"
cp -a "${TEST_DIR}/." "${RUN_TESTS}/"

# Hidden fixtures live under tests/ only — install at verifier time, never bake into the agent image.
rm -rf /opt/verifier-fixtures
mkdir -p /opt/verifier-fixtures
if [ -d "${RUN_TESTS}/verifier-fixtures" ]; then
  cp -a "${RUN_TESTS}/verifier-fixtures/." /opt/verifier-fixtures/
fi

# rebuild-amavis-lib: re-assert executable bits after agent edits (bash stack)
chmod +x /app/bin/amavis-quarantine /app/lib/*.sh /app/scripts/*.sh 2>/dev/null || true

set +e
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${RUN_TESTS}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
