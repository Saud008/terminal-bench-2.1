#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app
DIR="$(cd "$(dirname "$0")" && pwd)"
SOL="${DIR}/files"
cp -f "${SOL}/golden_map.go" /app/internal/revision/map.go
cp -f "${SOL}/golden_overlap.go" /app/internal/span/overlap.go
cp -f "${SOL}/golden_vote.go" /app/internal/weight/vote.go
cp -f "${SOL}/golden_precedence.go" /app/internal/lock/precedence.go
cp -f "${SOL}/golden_direction.go" /app/internal/relation/direction.go
cp -f "${SOL}/golden_export.go" /app/internal/export/consensus.go
for f in /app/internal/revision/map.go /app/internal/span/overlap.go /app/internal/weight/vote.go \
  /app/internal/lock/precedence.go /app/internal/relation/direction.go /app/internal/export/consensus.go; do
  sed -i 's/\r$//' "$f"
done
go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/bratctl ./cmd/bratctl
bash /app/scripts/reset-state.sh
