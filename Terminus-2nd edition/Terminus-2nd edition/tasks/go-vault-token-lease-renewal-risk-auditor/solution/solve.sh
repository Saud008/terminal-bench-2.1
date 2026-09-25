#!/bin/bash
# Oracle solve - task identity go-vault-token-lease-renewal-risk-auditor token 702cfb43
set -euo pipefail
cd "$(dirname "$0")"
export PATH="/usr/local/go/bin:${PATH}"

# Overlay corrected modules onto the agent tree.
while IFS= read -r -d '' src; do
  rel="${src#files/}"
  dest="/app/${rel}"
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
done < <(find files -type f -print0)

cd /app
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/vaultaud ./cmd/vaultaud
bash /app/scripts/reset-state.sh
TRANSCRIPT="${TB3_TRANSCRIPT_DIR:-/app/fixtures/renewal_logs}"
/app/bin/vaultaud audit --transcript-dir "$TRANSCRIPT" --config-dir /app/fixtures/config --staging /app/state/lease_audit_buffer.jsonl
/app/bin/vaultaud rollup --staging /app/state/lease_audit_buffer.jsonl --atlas /app/output/token_risk_rollup.json
