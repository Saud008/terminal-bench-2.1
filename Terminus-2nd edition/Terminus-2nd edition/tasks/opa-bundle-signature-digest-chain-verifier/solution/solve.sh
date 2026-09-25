#!/usr/bin/env bash
set -euo pipefail
SOL=""
for candidate in "$(dirname "$0")" "$(dirname "$0")/files" /solution /oracle/solution; do
  if [ -f "${candidate}/golden_digest.go" ]; then
    SOL="${candidate}"
    break
  fi
done
if [ -z "${SOL}" ]; then
  echo "golden sources not found" >&2
  exit 1
fi
cp -f "${SOL}/golden_canonical.go" /app/internal/bundle/canonical.go
cp -f "${SOL}/files/golden_ingest_preview.go" /app/internal/bundle/ingest_preview.go 2>/dev/null \
  || cp -f "${SOL}/golden_ingest_preview.go" /app/internal/bundle/ingest_preview.go
cp -f "${SOL}/golden_preview_ledger.go" /app/internal/bundle/preview_ledger.go
cp -f "${SOL}/golden_digest.go" /app/internal/verify/digest.go
cp -f "${SOL}/golden_scope.go" /app/internal/verify/scope.go
cp -f "${SOL}/golden_revoke.go" /app/internal/verify/revoke.go
cp -f "${SOL}/golden_trace.go" /app/internal/eval/trace.go
cp -f "${SOL}/golden_audit.go" /app/internal/eval/audit.go
export PATH="/usr/local/go/bin:${PATH}"
cd /app
go build -mod=readonly -o /usr/local/bin/bundlectl ./cmd/bundlectl
