#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":{"summary":{"tests":0,"passed":0,"failed":0,"pending":0,"skipped":0,"other":0}}}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

bash /app/scripts/reset-state.sh >/dev/null 2>&1
go build -mod=readonly -o /usr/local/bin/vtgatesim ./cmd/vtgatesim || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}
if ! bash /app/scripts/verifier-rebuild.sh >/dev/null 2>&1; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

set +e
/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
