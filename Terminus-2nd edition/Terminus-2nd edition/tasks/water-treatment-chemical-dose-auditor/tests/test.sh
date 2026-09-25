#!/usr/bin/env bash
set -euo pipefail

# conftest rebuild: cargo build --release before pytest

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

set +e
bash /app/scripts/rebuild-wtcdctl.sh && bash /app/scripts/reset-workspace.sh && python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_wtcda_ledger_lifecycle.py \
  /tests/test_wtcda_breach_atlas.py \
  /tests/test_wtcda_hidden_shift_probes.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
