#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution"; do
  if [ -f "${candidate}/internal/ingest/ingest.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "solution ingest.go not found" >&2; exit 1; }

cp -f "${SOL}/internal/ingest/ingest.go" /app/internal/ingest/ingest.go
cp -f "${SOL}/internal/replay/engine.go" /app/internal/replay/engine.go
cp -f "${SOL}/internal/export/compliance.go" /app/internal/export/compliance.go
cp -f "${SOL}/internal/fixparse/parse.go" /app/internal/fixparse/parse.go

for copied in \
  /app/internal/ingest/ingest.go \
  /app/internal/replay/engine.go \
  /app/internal/export/compliance.go \
  /app/internal/fixparse/parse.go; do
  sed -i 's/\r$//' "${copied}"
done

go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/dropcopyctl ./cmd/dropcopyctl
bash /app/scripts/reset-state.sh
test -x /app/bin/dropcopyctl
echo "dropcopy-session-bust-ledger oracle ready"
