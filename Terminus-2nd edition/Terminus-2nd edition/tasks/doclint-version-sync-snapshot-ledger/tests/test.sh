#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/cargo/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export CARGO_INCREMENTAL=0
export CARGO_NET_OFFLINE=true
TEST_DIR="${TEST_DIR:-/tests}"
export VERIFIER_BROKEN_MODEL="${TEST_DIR}/verifier-broken-docmodel"
export VERIFIER_BROKEN_SYNC="${TEST_DIR}/verifier-broken-docsync"
export VERIFIER_BROKEN_EXPORT="${TEST_DIR}/verifier-broken-docexport"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
echo '{"version":"1.0.0","results":{"tool":{"name":"pytest"},"summary":{"tests":0,"passed":0,"failed":0,"skipped":0},"tests":[]}}' > /logs/verifier/ctrf.json

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

for f in "${TEST_DIR}/test.sh" "${TEST_DIR}/"*.py; do
  if [ -f "$f" ]; then
    sed -i 's/\r$//' "$f" 2>/dev/null || true
  fi
done

for d in "${VERIFIER_BROKEN_MODEL}" "${VERIFIER_BROKEN_SYNC}" "${VERIFIER_BROKEN_EXPORT}" "${TEST_DIR}/verifier-golden"; do
  if [ -d "$d" ]; then
    for f in "$d"/*.rs; do
      if [ -f "$f" ]; then
        sed -i 's/\r$//' "$f" 2>/dev/null || true
      fi
    done
  fi
done

bash /app/scripts/reset-state.sh >/dev/null 2>&1

bash /app/scripts/build.sh >/dev/null 2>&1 || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

cargo build --offline --release --locked -p term-lsp >/dev/null 2>&1 || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

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
