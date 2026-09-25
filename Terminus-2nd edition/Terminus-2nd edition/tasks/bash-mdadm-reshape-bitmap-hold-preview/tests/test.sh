#!/usr/bin/env bash
# rebuild-mdreshape.sh also runs via tests/conftest.py session autouse before pytest.
if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
set +e
/opt/verifier-venv/bin/pytest --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_run_state_replay.py \
  /tests/test_policy_matrix.py \
  /tests/test_verifier_fixtures.py \
  /tests/test_subcommand_aliases.py \
  /tests/test_contract_math_units.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
