#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export PYTHONDONTWRITEBYTECODE=1
export VERIFIER_SEED="${VERIFIER_SEED:-tmpfiles-path-cleanup-age-guard-repair}"

TEST_DIR="${TEST_DIR:-/tests}"
RUN_TESTS="/tmp/tmpfiles-verifier-tests"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

rm -rf "${RUN_TESTS}"
mkdir -p "${RUN_TESTS}"
cp -a "${TEST_DIR}/." "${RUN_TESTS}/"

set +e
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${RUN_TESTS}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
