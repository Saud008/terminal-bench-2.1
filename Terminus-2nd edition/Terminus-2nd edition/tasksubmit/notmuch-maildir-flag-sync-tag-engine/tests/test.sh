#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export TERM="${TERM:-dumb}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /logs/artifacts /app/output
echo 0 > /logs/verifier/reward.txt
echo '{"version":"1.0.0","results":{"tool":{"name":"pytest"},"summary":{"tests":0,"passed":0,"failed":0,"skipped":0},"tests":[]}}' > /logs/verifier/ctrf.json

cd /app || exit 1

bash /app/scripts/reset-state.sh

# rebuild-verifier — compile agent-edited Go before pytest
if ! bash /app/scripts/verifier-rebuild.sh; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

set +e
pytest --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
