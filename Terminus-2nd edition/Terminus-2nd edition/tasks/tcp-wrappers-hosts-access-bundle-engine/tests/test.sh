#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
export VERIFIER_SEED="${VERIFIER_SEED:-tcp-wrappers-hosts-access-bundle-engine}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output
echo 0 > /logs/verifier/reward.txt
printf '%s\n' '{"results":{"tool":{"name":"pytest"},"summary":{"tests":0,"passed":0,"failed":0,"pending":0,"skipped":0,"other":0},"tests":[]}}' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

for f in "${TEST_DIR}/test.sh" /app/scripts/*.sh /app/lib/*.sh /app/bin/hostsctl; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
  fi
done

bash /app/scripts/reset-state.sh || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}
if ! bash /app/scripts/rebuild-hostsctl.sh; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

set +e
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
