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
  if [ -f "${candidate}/golden_pit.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_pit.go not found" >&2; exit 1; }

cp -f "${SOL}/golden_pit.go" /app/internal/join/pit.go
cp -f "${SOL}/golden_window.go" /app/internal/ttl/window.go
cp -f "${SOL}/golden_backfill.go" /app/internal/partition/backfill.go
cp -f "${SOL}/golden_compare.go" /app/internal/parity/compare.go
cp -f "${SOL}/golden_dedup.go" /app/internal/dedup/timestamp.go
cp -f "${SOL}/golden_export.go" /app/internal/export/report.go

for copied in \
  /app/internal/join/pit.go \
  /app/internal/ttl/window.go \
  /app/internal/partition/backfill.go \
  /app/internal/parity/compare.go \
  /app/internal/dedup/timestamp.go \
  /app/internal/export/report.go; do
  sed -i 's/\r$//' "${copied}"
done

go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/feastctl ./cmd/feastctl
rm -rf /app/state/pit-staging.json /app/work/parity.db /app/output/*
mkdir -p /app/state /app/work /app/output
test -x /usr/local/bin/feastctl
echo "feast-pit oracle ready"
