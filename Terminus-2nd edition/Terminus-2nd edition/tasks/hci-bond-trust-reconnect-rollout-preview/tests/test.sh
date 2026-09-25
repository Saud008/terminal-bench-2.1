#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

# /app/scripts/rebuild-hciroll.sh runs from tests/conftest.py session autouse before pytest.

set +e
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_fleet_scan_materialize.py \
  /tests/test_eligibility_gates.py \
  /tests/test_rank_ordering.py \
  /tests/test_atlas_digest_contract.py \
  /tests/test_cutover_publish.py \
  /tests/test_cli_load_alias.py \
  /tests/test_hidden_opt_fixtures.py \
  /tests/test_hciops_source_guards.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
