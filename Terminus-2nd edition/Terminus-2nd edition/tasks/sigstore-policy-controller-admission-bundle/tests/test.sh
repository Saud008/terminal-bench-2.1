#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

# Rebuild from /app, then leave /app before pytest so an agent-planted
# /app/pytest.py cannot shadow the real runner via `python -m pytest`.
cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

sed -i 's/\r$//' "${TEST_DIR}"/*.py "${TEST_DIR}"/*.sh 2>/dev/null || true
bash /app/scripts/reset-state.sh >/dev/null 2>&1 || true
if ! go build -mod=mod -o /usr/local/bin/slsacip ./cmd/slsacip; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

set +e
cd "${TEST_DIR}" || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}
/opt/verifier-venv/bin/pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" \
  "${TEST_DIR}/test_slsa_quorum_wave_reasons.py" \
  "${TEST_DIR}/test_slsa_partial_seal_probes.py" \
  "${TEST_DIR}/test_slsa_fixture_digest_locks.py" \
  "${TEST_DIR}/test_slsa_tb3_hidden_traps.py" \
  -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
