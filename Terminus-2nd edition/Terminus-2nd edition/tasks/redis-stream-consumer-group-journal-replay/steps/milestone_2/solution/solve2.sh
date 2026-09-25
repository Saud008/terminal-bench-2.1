#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cp "${DIR}/files/pending.go" /app/internal/claim/pending.go
cp "${DIR}/files/autoclaim.go" /app/internal/claim/autoclaim.go
cp "${DIR}/files/create.go" /app/internal/group/create.go
cd /app && go build -o /app/bin/redisctl ./cmd/redisctl
