# Oracle solve — task identity anticheat-heartbeat-sequence-gap-ledger token 3a242c0d
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
  if [ -f "${candidate}/continuity_gate.go" ]; then
    FILES_DIR="${candidate}"
    break
  fi
done

if [ -z "${FILES_DIR}" ]; then
  echo "oracle: solution/files/continuity_gate.go not found" >&2
  exit 1
fi

cd /app
install -m 644 "${FILES_DIR}/continuity_gate.go" internal/policy/continuity_gate.go
install -m 644 "${FILES_DIR}/trust_bind.go" internal/vault/trust_bind.go
install -m 644 "${FILES_DIR}/ban_revoke.go" internal/seal/ban_revoke.go
install -m 644 "${FILES_DIR}/chain_write.go" internal/witness/chain_write.go
install -m 644 "${FILES_DIR}/digest_emit.go" internal/export/digest_emit.go
install -m 644 "${FILES_DIR}/pin_clock.go" internal/clock/pin_clock.go

for f in internal/policy/continuity_gate.go internal/vault/trust_bind.go internal/seal/ban_revoke.go internal/witness/chain_write.go internal/export/digest_emit.go internal/clock/pin_clock.go; do
  sed -i 's/\r$//' "$f"
done

go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/livattest ./cmd/livattest
test -x /usr/local/bin/livattest
