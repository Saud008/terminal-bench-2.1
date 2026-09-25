#!/usr/bin/env bash
set -euo pipefail
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd /app

verify_oracle_targets() {
  local -a expected=(
    /app/internal/patronbar/cal.go
    /app/internal/priqueue/sort.go
    /app/internal/branchsel/select.go
    /app/internal/snaprollup/digestwire.go
    /app/internal/passmark/seal.go
    /app/internal/atlasledger/ledgeremit.go
  )
  local path
  for path in "${expected[@]}"; do
    test -f "${path}"
    test -s "${path}"
  done
}

bash "${ROOT_DIR}/apply_frontier.sh"
verify_oracle_targets
python3 /app/fixtures/build_scenarios.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/holdfairctl ./cmd/holdfairctl
test -x /app/bin/holdfairctl
echo "library-hold-queue-fairness-governor oracle ready"
