#!/usr/bin/env bash
# Oracle solve - bitswap-wantlist-session-seal-ledger
set -euo pipefail

APP="/app"
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_ROOT="${SCRIPT_DIR}/files/internal"

install_patch() {
  local rel="$1"
  local src="${PATCH_ROOT}/${rel}"
  local dest="${APP}/internal/${rel}"
  [[ -f "${src}" ]] || { echo "missing oracle patch ${src}" >&2; exit 1; }
  mkdir -p "$(dirname "${dest}")"
  install -m 0644 "${src}" "${dest}"
}

install_patch peerwant/merge.go
install_patch peerwant/cancel.go
install_patch creditline/credit.go
install_patch session/timeout.go
install_patch schedhead/queue.go
install_patch export/session_report_emit.go
install_patch traceplay/event_journal.go

cd "${APP}"
go build -mod=readonly -o /usr/local/bin/wantplay ./cmd/wantplay
bash /app/scripts/reset-state.sh
test -x /usr/local/bin/wantplay
echo "wantplay oracle ready"