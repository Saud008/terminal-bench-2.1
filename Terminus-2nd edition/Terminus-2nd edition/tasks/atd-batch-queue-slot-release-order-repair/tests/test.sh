#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /app/output
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script."
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

bash /app/scripts/reset-state.sh || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

VERIFIER_GOLDEN_LIB="$(mktemp -d /tmp/atd-vgl.XXXXXX)"
export VERIFIER_GOLDEN_LIB
if ! cp "${TEST_DIR}/golden_lib/"golden_*.sh "${VERIFIER_GOLDEN_LIB}/"; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi
chmod -R go-rwx "${VERIFIER_GOLDEN_LIB}"
chmod u+rx "${VERIFIER_GOLDEN_LIB}"
find "${VERIFIER_GOLDEN_LIB}" -type f -exec chmod u+rw,go-rwx {} +

set +e
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
rc=$?
if [ "$rc" -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
