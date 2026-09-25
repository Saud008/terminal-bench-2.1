#!/usr/bin/env bash
# rebuild-rsyncprev.sh runs via tests/conftest.py session autouse before pytest.
if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
set +e
/opt/verifier-venv/bin/pytest --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_rsyncprev_compiled_suite.py \
  /tests/test_rsyncprev_hidden_suite.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
