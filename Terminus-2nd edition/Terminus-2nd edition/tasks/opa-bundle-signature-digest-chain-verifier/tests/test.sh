#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=0
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

sed -i 's/\r$//' "${TEST_DIR}"/*.py "${TEST_DIR}"/*.sh 2>/dev/null || true
bash /app/scripts/reset-state.sh >/dev/null 2>&1 || true
if ! bash /app/scripts/rebuild-bundlectl.sh; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

set +e
cd "${TEST_DIR}" || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}
/opt/verifier-venv/bin/pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" \
  -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
