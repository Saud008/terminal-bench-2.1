#!/bin/bash
set -euo pipefail

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
    exit 1
fi

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

set +e
cd /app/environment && cargo build --release --locked -p wbleguard && install -D -m 0755 target/release/wbleguard /app/environment/bin/wbleguard && pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
