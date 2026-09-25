#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export TERM="${TERM:-dumb}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /logs/artifacts /app/output
echo 0 > /logs/verifier/reward.txt
printf '%s\n' '{"version":"1.0.0","results":{"summary":{"tests":0,"pending":0,"pass":0,"fail":0,"skipped":0},"tests":[]}}' \
  > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ] || [ -z "${PWD:-}" ]; then
  echo "Error: No working directory set. Please set WORKDIR in your Dockerfile before running this script." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

if [ ! -x /app/bin/stage2-audit ]; then
  echo "Error: stage2-audit CLI missing" >&2
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

for f in "${TEST_DIR}/test.sh" "${TEST_DIR}/"*.py /app/scripts/*.sh; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
  fi
done
for d in "${TEST_DIR}/verifier-broken" "${TEST_DIR}/verifier-golden"; do
  if [ -d "$d" ]; then
    for f in "$d"/*.sh; do
      [ -f "$f" ] && sed -i 's/\r$//' "$f" 2>/dev/null || true
    done
  fi
done

bash /app/scripts/reset-state.sh
bash /app/scripts/rebuild-lib.sh

set +e
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
