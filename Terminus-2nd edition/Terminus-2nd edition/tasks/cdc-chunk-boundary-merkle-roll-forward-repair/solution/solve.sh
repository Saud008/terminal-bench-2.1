#!/usr/bin/env bash
set -euo pipefail

APP="/app"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_cdc.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_cdc.go not found" >&2; exit 1; }

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export GOCACHE="${GOCACHE:-/opt/gocache}"
export GOFLAGS="${GOFLAGS:--mod=readonly}"

cp -f "${SOL}/golden_config.go" "${APP}/internal/config/params.go"
cp -f "${SOL}/golden_cdc.go" "${APP}/internal/chunk/cdc.go"
cp -f "${SOL}/golden_merkle.go" "${APP}/internal/merkle/tree.go"
cp -f "${SOL}/golden_checkpoint.go" "${APP}/internal/checkpoint/state.go"
cp -f "${SOL}/golden_engine.go" "${APP}/internal/roll/engine.go"

cd "${APP}"
go build -mod=readonly -o /usr/local/bin/cdcctl ./cmd/cdcctl
bash /app/scripts/reset-state.sh
echo "cdcctl oracle ready"
