#!/usr/bin/env bash
# rebuild-zfshold.sh also runs via tests/conftest.py session autouse before pytest.
if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
bash /app/scripts/rebuild-zfshold.sh >/dev/null
set +e
/opt/verifier-venv/bin/pytest --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_ledger_persistence.py \
  /tests/test_gates_suite.py \
  /tests/test_hidden_traps.py \
  /tests/test_cli_aliases.py \
  /tests/test_reference_math_unit.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
