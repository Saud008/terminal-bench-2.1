#!/usr/bin/env bash
set -euo pipefail
cd /app
go build -mod=readonly -o /usr/local/bin/pulsar-dedup-replay ./cmd/pulsar-dedup-replay
