#!/usr/bin/env bash
set -euo pipefail

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

# go build runs in tests/conftest.py pytest_configure before pytest (rebuild layerfuse from /app sources)

set +e
python3 -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_outputs.py \
    /tests/layer_catalog_behavior_tests.py \
    /tests/atlas_publish_trap_tests.py \
    -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
