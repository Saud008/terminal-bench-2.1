#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
echo '{"version":"1.0.0","results":{"tool":{"name":"pytest"},"summary":{"tests":0,"passed":0,"failed":0,"skipped":0},"tests":[]}}' > /logs/verifier/ctrf.json
# Reward channel is root-only; agent UID (rebuild/binary) cannot forge reward.txt.
chmod 700 /logs/verifier

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

cd /app || exit 1

# Rebuild candidate sources as the unprivileged agent; root installs the system binary.
set +e
runuser -u agent -- env PATH="/usr/local/cargo/bin:${PATH}" \
  cargo build --offline --release --locked -p srtctl
BUILD_RC=$?
if [ "$BUILD_RC" -ne 0 ]; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi
install -o root -g root -m 0755 /app/target/release/srtctl /usr/local/bin/srtctl

# Pytest stays root-owned via /opt/verifier-venv; CLI invocations drop to agent in tests.
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
