#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"

mkdir -p /logs/verifier /logs/artifacts /app/output
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ] || [ -z "${PWD:-}" ]; then
  echo "Error: No working directory set. Please set WORKDIR in your Dockerfile before running this script." >&2
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 0
}

TEST_DIR="${TEST_DIR:-/tests}"

for f in "${TEST_DIR}/test.sh" /app/scripts/*.sh; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
  fi
done

mkdir -p /opt/verifier-fixtures
if [ -d "${TEST_DIR}/verifier-fixtures" ]; then
  cp -a "${TEST_DIR}/verifier-fixtures/." /opt/verifier-fixtures/
fi

if ! cargo build --locked --release -p fc-alias-check; then
  echo 0 > /logs/verifier/reward.txt
  exit 0
fi
install -m 0755 target/release/fc-alias-check /usr/local/bin/fc-alias-check

PYTEST_TARGETS=("${TEST_DIR}/test_outputs.py")
if [ "${AUTHOR_VALIDATION:-0}" = "1" ]; then
  PYTEST_TARGETS+=("${TEST_DIR}/author_validation.py")
fi

set +e
/opt/verifier-venv/bin/python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json "${PYTEST_TARGETS[@]}" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
