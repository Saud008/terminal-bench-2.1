#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_merge.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden sources not found" >&2; exit 1; }

cp -f "${SOL}/golden_merge.go" /app/internal/rrule/merge.go
cp -f "${SOL}/golden_zone.go" /app/internal/timezone/zone.go
cp -f "${SOL}/golden_setpos.go" /app/internal/rrule/setpos.go
cp -f "${SOL}/golden_until.go" /app/internal/rrule/until.go
cp -f "${SOL}/golden_engine.go" /app/internal/rrule/engine.go
cp -f "${SOL}/golden_weekly.go" /app/internal/rrule/weekly.go

go build -mod=readonly -o /usr/local/bin/expand ./cmd/expand
