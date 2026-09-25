#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output /app/state
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

set +e
bash /app/scripts/reset-state.sh
RESET_RC=$?
cargo build --release --locked -p nmeapipeline
BUILD_RC=$?
install -m 0755 /app/target/release/nmeapipeline /usr/local/bin/nmeapipeline
INSTALL_RC=$?
[ "$RESET_RC" -eq 0 ] && [ "$BUILD_RC" -eq 0 ] && [ "$INSTALL_RC" -eq 0 ] && \
  /opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
