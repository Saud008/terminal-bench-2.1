#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
# Reward channel is root-only; agent UID (rebuild/binary) cannot forge reward.txt.
chmod 700 /logs/verifier

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  exit 1
fi

# Verifier rebuild contract: conftest runs verifier-rebuild.sh as user agent before pytest.
# Pytest and /opt/verifier-venv stay root-owned; CLI invocations drop to agent via runuser.

set +e
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "/tests/test_tbice_smoke.py" \
  "/tests/test_tbice_catalog_contract.py" \
  "/tests/test_tbice_retention_audit.py" \
  "/tests/test_tbice_publish_expiry.py" \
  "/tests/test_tbice_overlay_traps.py" -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
