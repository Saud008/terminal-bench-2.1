#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
  exit 1
fi

export VERIFIER_SEED="${VERIFIER_SEED:-casbin-seed-1}"
export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

TEST_DIR="${TEST_DIR:-/tests}"

# Verifier-only ground truth: mount at test time, not in the agent image.
mkdir -p /opt/verifier-casctl /opt/verifier-casctl-layers /opt/verifier-casctl-math
cp "${TEST_DIR}/verifier/casctl.json" /opt/verifier-casctl/casctl.json
cp "${TEST_DIR}/verifier/layers/"*.go /opt/verifier-casctl-layers/
cp "${TEST_DIR}/verifier/casbin_batch_math.py" /opt/verifier-casctl-math/casbin_batch_math.py
chmod 700 /opt/verifier-casctl /opt/verifier-casctl-layers /opt/verifier-casctl-math
chmod 600 /opt/verifier-casctl/casctl.json /opt/verifier-casctl-layers/*.go /opt/verifier-casctl-math/casbin_batch_math.py

cd /app
go build -mod=readonly -o /usr/local/bin/casctl ./cmd/casctl

set +e
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
