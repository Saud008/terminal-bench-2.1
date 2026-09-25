#!/usr/bin/env bash
set -euo pipefail
cd /app
go build -o /usr/local/bin/cuectl ./cmd/cuectl
