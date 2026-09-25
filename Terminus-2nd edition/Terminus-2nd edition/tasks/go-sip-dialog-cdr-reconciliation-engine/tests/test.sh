#!/usr/bin/env bash
# rebuild-sipcdr.sh runs inside sip_transcript_runner.reset_carrier_workspace before each pytest case.
if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
set +e
pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py /tests/test_sip_cdr_contracts.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
