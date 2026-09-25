#!/usr/bin/env bash
if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
rebuild-geoboxplay.sh >/dev/null
set +e
/opt/verifier-venv/bin/python -m pytest --ctrf /logs/verifier/ctrf.json \
  /tests/test_outputs.py \
  /tests/test_load_seq_and_salt.py \
  /tests/test_policy_matrix.py \
  /tests/test_hidden_overlays.py \
  /tests/test_synonym_verbs.py \
  /tests/test_authority_units.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
