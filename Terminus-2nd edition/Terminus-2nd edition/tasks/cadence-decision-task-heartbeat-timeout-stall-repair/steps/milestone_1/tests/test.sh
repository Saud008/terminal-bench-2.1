#!/bin/bash

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":{"summary":{"tests":0,"passed":0,"failed":0,"pending":0,"skipped":0,"other":0}}}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export PYTHONPATH="/opt/verifier-scripts:${PYTHONPATH:-}"
TEST_DIR="${TEST_DIR:-/tests}"

cd /app || {
    echo 0 > /logs/verifier/reward.txt
    exit 1
}

bash /app/scripts/reset-state.sh

set +e
go build -mod=readonly -o /usr/local/bin/cadence-replay ./cmd/cadence-replay || {
    echo 0 > /logs/verifier/reward.txt
    exit 1
}
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_m1.py" -rA
if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
