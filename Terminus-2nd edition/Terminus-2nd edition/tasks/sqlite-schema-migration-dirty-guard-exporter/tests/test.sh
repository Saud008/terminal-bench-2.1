#!/usr/bin/env bash
set -euo pipefail

mkdir -p /logs/verifier /app/state /app/output /app/bin

printf '%s\n' '{"version":"1.0.0","results":{"summary":{"tests":0,"passed":0,"failed":0,"pending":0,"skipped":0,"other":0}}}}' > /logs/verifier/ctrf.json
echo 0 > /logs/verifier/reward.txt

cd /app || {
    echo 0 > /logs/verifier/reward.txt
    exit 1
}

if ! command -v go >/dev/null 2>&1; then
    if [ ! -x /app/bin/migratectl ]; then
        echo 0 > /logs/verifier/reward.txt
        exit 1
    fi
elif ! go mod tidy && go build -o /app/bin/migratectl ./cmd/migratectl; then
    echo 0 > /logs/verifier/reward.txt
    exit 1
fi

set +e
/opt/verifier-venv/bin/python -m pytest -rA -o cache_dir=/tmp/pytest_cache \
    --ctrf /logs/verifier/ctrf.json "${TEST_DIR:-/tests}/test_outputs.py"
if [ $? -eq 0 ]; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
