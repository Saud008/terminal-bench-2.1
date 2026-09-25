#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/go/bin:/usr/local/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

bash /app/scripts/reset-state.sh

go build -mod=readonly -o /usr/local/bin/grpcfaultd ./cmd/grpcfaultd
BUILD_SERVER_RC=$?
go build -mod=readonly -o /usr/local/bin/frameprobe ./cmd/frameprobe
BUILD_PROBE_RC=$?

bash /app/scripts/start-server.sh
START_RC=$?

set +e
[ "$BUILD_SERVER_RC" -eq 0 ] && [ "$BUILD_PROBE_RC" -eq 0 ] && [ "$START_RC" -eq 0 ] && \
  /opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
