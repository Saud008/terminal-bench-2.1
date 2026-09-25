# Oracle solve — task identity cue-default-disjunction-vet-trace-engine token 6e79771b
#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="${APP_ROOT:-/app}"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT="${SCRIPT_DIR}/files/cuewrap"
DEST="${APP_ROOT}/internal/cuewrap"
BROKEN="/opt/verifier-broken-cuewrap"

for mod in disjunct closed embed compose snapshot_bind snapshot_guard vet export; do
  cmp -s "${BROKEN}/${mod}.go" "${DEST}/${mod}.go" || {
    echo "expected broken baseline for ${mod}.go" >&2
    exit 1
  }
done

install -m 0644 "${PATCH_ROOT}/disjunct.go" "${DEST}/disjunct.go"
install -m 0644 "${PATCH_ROOT}/closed.go" "${DEST}/closed.go"
install -m 0644 "${PATCH_ROOT}/embed.go" "${DEST}/embed.go"
install -m 0644 "${PATCH_ROOT}/compose.go" "${DEST}/compose.go"
install -m 0644 "${PATCH_ROOT}/snapshot_bind.go" "${DEST}/snapshot_bind.go"
install -m 0644 "${PATCH_ROOT}/snapshot_guard.go" "${DEST}/snapshot_guard.go"
install -m 0644 "${PATCH_ROOT}/diag_linefmt.go" "${DEST}/diag_linefmt.go"
install -m 0644 "${PATCH_ROOT}/vet.go" "${DEST}/vet.go"
install -m 0644 "${PATCH_ROOT}/export.go" "${DEST}/export.go"

cd "${APP_ROOT}"
go build -o /usr/local/bin/cuectl ./cmd/cuectl

bash /app/scripts/reset-state.sh
