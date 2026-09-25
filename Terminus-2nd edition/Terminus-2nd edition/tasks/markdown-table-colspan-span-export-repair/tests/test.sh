#!/usr/bin/env bash

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
    echo "Error: No working directory set. Please set WORKDIR in your Dockerfile before running this script."
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

cd /app || {
    echo 0 > /logs/verifier/reward.txt
    exit 1
}

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export VERIFIER_SEED="${VERIFIER_SEED:-markdown-table-colspan-span-export-repair}"
TEST_DIR="${TEST_DIR:-/tests}"

set +e
cargo build --release --locked --offline -p mdtable
BUILD_RC=$?
install -m 0755 /app/target/release/mdtable /usr/local/bin/mdtable 2>/dev/null || true

/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
PYTEST_RC=$?

[ "$BUILD_RC" -eq 0 ] && [ "$PYTEST_RC" -eq 0 ]
if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
