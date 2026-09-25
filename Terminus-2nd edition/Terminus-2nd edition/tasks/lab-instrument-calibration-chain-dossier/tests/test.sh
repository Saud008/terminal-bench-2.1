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
python3 -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_calbind_intake_contract.py \
  /tests/test_register_fusion_boundary.py \
  /tests/test_dossier_render_math.py \
  /tests/test_hidden_metrology_traps.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
