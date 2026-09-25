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
cp -f "${SOL}/golden_revision.go" /app/internal/rules/revision.go
cp -f "${SOL}/golden_window.go" /app/internal/suppression/window.go
cp -f "${SOL}/golden_hash.go" /app/internal/dedupe/hash.go
cp -f "${SOL}/golden_escalate.go" /app/internal/criticality/escalate.go
cp -f "${SOL}/golden_lifecycle.go" /app/internal/quarantine/lifecycle.go
cp -f "${SOL}/golden_export.go" /app/internal/export/bundle.go

for copied in \
  /app/internal/ingest/stage.go \
  /app/internal/rules/revision.go \
  /app/internal/suppression/window.go \
  /app/internal/dedupe/hash.go \
  /app/internal/criticality/escalate.go \
  /app/internal/quarantine/lifecycle.go \
  /app/internal/export/bundle.go; do
  sed -i 's/\r$//' "${copied}"
done

go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/yaracor ./cmd/yaracor
bash /app/scripts/reset-state.sh

test -x /usr/local/bin/yaracor
echo "yaracor oracle ready"
