#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
go build -mod=vendor -trimpath -ldflags="-s -w" -o /usr/local/bin/kongadmit ./cmd/kongadmit
