#!/usr/bin/env bash
set -euo pipefail
cd /app
go build -mod=readonly -o /usr/local/bin/temporal-signal-replay ./cmd/temporal-signal-replay
