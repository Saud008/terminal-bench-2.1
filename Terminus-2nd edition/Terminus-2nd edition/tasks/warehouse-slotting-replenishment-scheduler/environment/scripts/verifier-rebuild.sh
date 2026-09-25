#!/usr/bin/env bash
set -euo pipefail
cd /app
python3 /app/fixtures/build_warehouse_yard.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/whslot ./cmd/whslot
