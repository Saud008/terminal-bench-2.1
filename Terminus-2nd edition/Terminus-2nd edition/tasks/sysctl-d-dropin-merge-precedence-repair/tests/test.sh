#!/usr/bin/env bash
set -uo pipefail

export PATH="/opt/verifier-venv/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
export TERM="${TERM:-dumb}"
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier /logs/artifacts /app/output
echo 0 > /logs/verifier/reward.txt
printf '%s\n' '{"version":"1.0.0","results":{"summary":{"tests":0,"pending":0,"pass":0,"fail":0,"skipped":0},"tests":[]}}' \
  > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ] || [ -z "${PWD:-}" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile before running this script." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

if [ ! -x /usr/local/bin/sysctlmerge ]; then
  echo "Error: sysctlmerge CLI missing" >&2
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

if [ -f "${TEST_DIR}/test_outputs.py" ] && grep -q $'\r' "${TEST_DIR}/test_outputs.py" 2>/dev/null; then
  FIX_DIR="/tmp/vtests-$$"
  mkdir -p "${FIX_DIR}"
  tr -d '\r' < "${TEST_DIR}/test_outputs.py" > "${FIX_DIR}/test_outputs.py"
  cp "${TEST_DIR}/reference_merger.py" "${FIX_DIR}/reference_merger.py" 2>/dev/null || true
  cp "${TEST_DIR}/bundle_builder.py" "${FIX_DIR}/bundle_builder.py" 2>/dev/null || true
  for d in verifier-broken verifier-golden patches; do
    if [ -d "${TEST_DIR}/${d}" ]; then
      cp -a "${TEST_DIR}/${d}" "${FIX_DIR}/${d}"
    fi
  done
  TEST_DIR="${FIX_DIR}"
fi

for f in "${TEST_DIR}/test.sh" "${TEST_DIR}/"*.py /app/scripts/*.sh; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
  fi
done

bash /app/scripts/reset-state.sh

set +e
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
