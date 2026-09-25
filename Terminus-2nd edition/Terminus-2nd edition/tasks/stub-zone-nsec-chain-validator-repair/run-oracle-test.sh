#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:/usr/sbin:/usr/bin:/bin:${PATH}"

cp -f /solution/golden_order.go /app/internal/nsec/order.go
cp -f /solution/golden_hash.go /app/internal/nsec3/hash.go
cp -f /solution/golden_cache.go /app/internal/stub/cache.go
cp -f /solution/golden_walker.go /app/internal/proof/walker.go

cd /app
go build -mod=readonly -o /usr/local/bin/nsecval ./cmd/nsecval

mkdir -p /opt/verifier-fixtures /tests-run
cp -a /tests/. /tests-run/
find /tests-run -type f \( -name '*.sh' -o -name '*.py' \) -exec sed -i 's/\x0d$//' {} +

mkdir -p /opt/verifier-fixtures
cp -a /tests-run/verifier-fixtures/. /opt/verifier-fixtures/

export TEST_DIR=/tests-run
bash /tests-run/test.sh
echo "REWARD=$(cat /logs/verifier/reward.txt)"
