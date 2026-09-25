#!/usr/bin/env bash
set -euo pipefail

export VERIFIER_SEED="${VERIFIER_SEED:-verifier-run}"
export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export GOFLAGS="${GOFLAGS:--mod=vendor}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ] || [ -z "${PWD:-}" ]; then
  echo "Error: No working directory set. Please set WORKDIR in your Dockerfile before running this script." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

TEST_DIR="${TEST_DIR:-/tests}"

set +e
go build -mod=vendor -o /usr/local/bin/radiusproxy ./cmd/radiusproxy
if [ $? -ne 0 ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
