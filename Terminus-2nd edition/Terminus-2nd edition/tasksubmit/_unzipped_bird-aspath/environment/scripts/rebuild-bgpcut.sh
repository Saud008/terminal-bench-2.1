#!/usr/bin/env bash
set -euo pipefail
cd /app
/usr/local/go/bin/go build -o /usr/local/bin/bgpcut ./cmd/bgpcut
