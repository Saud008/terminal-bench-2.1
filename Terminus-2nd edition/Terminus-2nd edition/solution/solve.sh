#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=0
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution/files"; do
  if [ -f "${candidate}/golden_canon.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_canon.go not found" >&2; exit 1; }

mkdir -p /app/internal/audit

cp -f "${SOL}/golden_canon.go" /app/internal/audit/canon.go
cp -f "${SOL}/golden_ledger.go" /app/internal/audit/ledger.go
cp -f "${SOL}/golden_stage.go" /app/internal/party/stage.go
cp -f "${SOL}/golden_publish.go" /app/internal/party/publish.go
cp -f "${SOL}/golden_sweeper.go" /app/internal/cleanup/sweeper.go
cp -f "${SOL}/golden_query.go" /app/internal/store/query.go

for copied in \
  /app/internal/audit/canon.go \
  /app/internal/audit/ledger.go \
  /app/internal/party/stage.go \
  /app/internal/party/publish.go \
  /app/internal/cleanup/sweeper.go \
  /app/internal/store/query.go; do
  sed -i 's/\r$//' "${copied}"
done

go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/partyd ./cmd/partyd
bash /app/scripts/reset-state.sh

test -x /usr/local/bin/partyd
echo "party-audit-governor oracle ready"
