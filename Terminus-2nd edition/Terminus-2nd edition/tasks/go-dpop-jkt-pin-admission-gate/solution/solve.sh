# Oracle solve — task identity go-dpop-jkt-pin-admission-gate token 92ac16d5
#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=0

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES_DIR=""
for candidate in \
  "${SCRIPT_DIR}/files" \
  "/solution/files" \
  "/oracle/solution/files" \
  "/task/solution/files"; do
  if [ -f "${candidate}/proof_check.go" ]; then
    FILES_DIR="${candidate}"
    break
  fi
done

if [ -z "${FILES_DIR}" ]; then
  echo "oracle: solution/files/proof_check.go not found" >&2
  exit 1
fi

# Copy off possibly-flaky bind mounts before install (Docker Desktop).
STAGE="$(mktemp -d)"
trap 'rm -rf "${STAGE}"' EXIT
cp -f "${FILES_DIR}/proof_check.go" "${STAGE}/proof_check.go"
cp -f "${FILES_DIR}/pin_registry.go" "${STAGE}/pin_registry.go"
cp -f "${FILES_DIR}/jti_ledger.go" "${STAGE}/jti_ledger.go"
cp -f "${FILES_DIR}/chainhead_stage.go" "${STAGE}/chainhead_stage.go"
cp -f "${FILES_DIR}/deny_ledger_seal.go" "${STAGE}/deny_ledger_seal.go"
for f in "${STAGE}"/*.go; do
  sed -i 's/\r$//' "$f"
done

cd /app
install -m 644 "${STAGE}/proof_check.go" internal/proofparse/proof_check.go
install -m 644 "${STAGE}/pin_registry.go" internal/jktpin/pin_registry.go
install -m 644 "${STAGE}/jti_ledger.go" internal/jtiledger/jti_ledger.go
install -m 644 "${STAGE}/chainhead_stage.go" internal/chainhead/chainhead_stage.go
install -m 644 "${STAGE}/deny_ledger_seal.go" internal/auditseal/deny_ledger_seal.go

go build -trimpath -ldflags="-s -w" -o /usr/local/bin/jktadmit ./cmd/jktadmit
cp /usr/local/bin/jktadmit /app/bin/jktadmit
test -x /usr/local/bin/jktadmit
echo "oracle: jktadmit rebuilt"
