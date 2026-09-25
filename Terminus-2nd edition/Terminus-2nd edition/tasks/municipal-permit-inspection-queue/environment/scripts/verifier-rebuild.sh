#!/usr/bin/env bash
set -euo pipefail
python3 /app/fixtures/build_permit_bundles.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/mpiqctl ./cmd/mpiqctl
