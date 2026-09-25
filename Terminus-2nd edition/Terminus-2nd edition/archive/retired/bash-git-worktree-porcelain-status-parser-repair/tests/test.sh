#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ] || [ -z "${PWD:-}" ]; then
  echo "Error: No working directory set. Please set WORKDIR in your Dockerfile before running this script." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

for f in "${TEST_DIR}/test.sh" /app/scripts/*.sh /app/lib/*.sh /app/bin/wtstatus-export; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
  fi
done

bash /app/scripts/verifier-rebuild.sh
bash /app/scripts/reset-state.sh

set +e
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
