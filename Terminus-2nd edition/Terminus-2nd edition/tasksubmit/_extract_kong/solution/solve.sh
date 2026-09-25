#!/usr/bin/env bash
if grep -q $'\r' "$0" 2>/dev/null; then
  sed -i 's/\r$//' "$0"
  exec bash "$0" "$@"
fi
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
DIR="$(cd "$(dirname "$0")" && pwd)"
cp "${DIR}/patches/ingest.go" /app/internal/ingest/ingest.go
cp "${DIR}/patches/matcher.go" /app/internal/match/matcher.go
cp "${DIR}/patches/merge.go" /app/internal/merge/merge.go
cp "${DIR}/patches/chain.go" /app/internal/chain/chain.go
cp "${DIR}/patches/openapi.go" /app/internal/export/openapi.go
cp "${DIR}/patches/jwt.go" /app/internal/auth/jwt.go
bash /app/scripts/verifier-rebuild.sh
test -x /usr/local/bin/kongadmit
