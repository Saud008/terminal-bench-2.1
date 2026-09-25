#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /app/state /app/output
echo 0 > /logs/verifier/reward.txt

# rebuild-rpm-attest: refresh bash modules before behavioral pytest
bash /app/scripts/verifier-rebuild.sh
chmod +x /app/bin/rpm-repo-attest /app/lib/*.sh /app/lib/decoy/*.sh /app/lib/staging/*.sh 2>/dev/null || true

set +e
python3 -m pytest \
    -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json \
    /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
