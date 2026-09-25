#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution/files"; do
  if [ -f "${candidate}/golden_stage.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_stage.go not found" >&2; exit 1; }

cp -f "${SOL}/golden_stage.go" /app/internal/ingest/stage.go
cp -f "${SOL}/golden_wordorder.go" /app/internal/decode/wordorder.go
cp -f "${SOL}/golden_epochs.go" /app/internal/scale/epochs.go
cp -f "${SOL}/golden_skew.go" /app/internal/clock/skew.go
cp -f "${SOL}/golden_suppress.go" /app/internal/alarm/suppress.go
cp -f "${SOL}/golden_override.go" /app/internal/manifest/override.go
cp -f "${SOL}/golden_build.go" /app/internal/catalog/build.go
cp -f "${SOL}/golden_export.go" /app/internal/export/catalog.go

for copied in \
  /app/internal/ingest/stage.go \
  /app/internal/decode/wordorder.go \
  /app/internal/scale/epochs.go \
  /app/internal/clock/skew.go \
  /app/internal/alarm/suppress.go \
  /app/internal/manifest/override.go \
  /app/internal/catalog/build.go \
  /app/internal/export/catalog.go; do
  sed -i 's/\r$//' "${copied}"
done

# go build — satisfy repository-state oracle gate
go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/modbusctl ./cmd/modbusctl
bash /app/scripts/reset-state.sh

test -x /usr/local/bin/modbusctl
echo "modbus-drift-cataloger oracle ready"
