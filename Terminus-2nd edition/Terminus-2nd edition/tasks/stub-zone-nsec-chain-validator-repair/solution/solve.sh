#!/usr/bin/env bash
set -euo pipefail

APP="/app"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution" "/oracle/solution"; do
  if [ -f "${candidate}/golden_order.go" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "golden_order.go not found" >&2; exit 1; }

cp -f "${SOL}/golden_order.go" "${APP}/internal/nsec/order.go"
cp -f "${SOL}/golden_hash.go" "${APP}/internal/nsec3/hash.go"
cp -f "${SOL}/golden_cache.go" "${APP}/internal/stub/cache.go"
cp -f "${SOL}/golden_walker.go" "${APP}/internal/proof/walker.go"

cd "${APP}"
go build -mod=readonly -o /usr/local/bin/nsecval ./cmd/nsecval
bash /app/scripts/reset-state.sh
echo "nsecval oracle ready"
