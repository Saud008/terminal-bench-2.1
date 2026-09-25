#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app
bash "${ROOT_DIR}/apply_whslot.sh"
python3 /app/fixtures/build_warehouse_yard.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/whslot ./cmd/whslot
test -x /app/bin/whslot
echo "warehouse-slotting-replenishment-scheduler oracle ready"
