#!/usr/bin/env bash
# Oracle solve — task identity passport-visa-validity-window-ledger
set -euo pipefail

APP="/app"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${APP}"

apply_patch() {
  local patch_file="$1"
  if patch -p1 --forward --silent --dry-run < "${patch_file}" >/dev/null 2>&1; then
    patch -p1 --forward --silent < "${patch_file}"
  elif patch -p1 --reverse --silent --dry-run < "${patch_file}" >/dev/null 2>&1; then
    : # already applied
  else
    echo "oracle patch failed: $(basename "${patch_file}")" >&2
    return 1
  fi
}

for patch_name in \
  passport-validity.patch \
  visa-overlap.patch \
  entry-stay.patch \
  rule-precedence.patch \
  revoke-suppress.patch \
  watchlist-hold.patch \
  ledger-idempotent.patch; do
  apply_patch "${ROOT_DIR}/patches/${patch_name}"
done

find "${APP}/internal" "${APP}/cmd" -name '*.go' -exec sed -i 's/\r$//' {} +

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/borderdocctl ./cmd/borderdocctl
test -x /app/bin/borderdocctl
bash /app/scripts/reset-state.sh
echo "passport-visa-validity-window-ledger oracle ready"
