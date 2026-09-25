# Oracle solve — task identity passport-visa-validity-window-ledger
#!/usr/bin/env bash
set -euo pipefail

APP="/app"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${APP}"

patch -p1 --forward --silent < "${ROOT_DIR}/patches/passport-validity.patch" || true
patch -p1 --forward --silent < "${ROOT_DIR}/patches/visa-overlap.patch" || true
patch -p1 --forward --silent < "${ROOT_DIR}/patches/entry-stay.patch" || true
patch -p1 --forward --silent < "${ROOT_DIR}/patches/rule-precedence.patch" || true
patch -p1 --forward --silent < "${ROOT_DIR}/patches/revoke-suppress.patch" || true
patch -p1 --forward --silent < "${ROOT_DIR}/patches/watchlist-hold.patch" || true
patch -p1 --forward --silent < "${ROOT_DIR}/patches/ledger-idempotent.patch" || true

find "${APP}/internal" "${APP}/cmd" -name '*.go' -exec sed -i 's/\r$//' {} +

PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
python3 /app/fixtures/build_fixtures.py
go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/borderdocctl ./cmd/borderdocctl
test -x /app/bin/borderdocctl
bash /app/scripts/reset-state.sh
echo "passport-visa-validity-window-ledger oracle ready"
