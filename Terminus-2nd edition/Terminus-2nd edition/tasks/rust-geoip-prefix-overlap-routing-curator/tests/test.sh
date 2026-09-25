#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

# Verifier rebuild: cargo build --release --locked from /app (session conftest).
# Invoke installed pytest console script from /tests so agent-writable /app/pytest.py
# cannot satisfy python -m pytest. PYTHONSAFEPATH=1 + --confcutdir=/tests keep
# import/conftest discovery off the agent tree.
cd /tests
set +e
PYTHONSAFEPATH=1 /usr/local/bin/pytest \
  --confcutdir=/tests \
  -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_geocur_wal_snapshots.py \
  /tests/test_geocur_atlas_exports.py \
  /tests/test_geocur_supplemental_matrix.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
