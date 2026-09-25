#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export VERIFIER_SEED="${VERIFIER_SEED:-ent-edge-seed-7}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

for f in "${TEST_DIR}/test.sh" "${TEST_DIR}/"/*.py /app/scripts/*.sh; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
  fi
done

bash /app/scripts/reset-state.sh >/dev/null 2>&1
if ! bash /app/scripts/verifier-rebuild.sh >/dev/null 2>&1; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

set +e
/opt/verifier-venv/bin/python -m pytest \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
