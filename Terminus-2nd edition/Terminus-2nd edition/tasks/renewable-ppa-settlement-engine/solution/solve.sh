#!/usr/bin/env bash
# Oracle — renewable PPA interval settlement (token be360fc5)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

cd /app
test -f go.mod
grep -q 'github.com/terminus/ppareconctl' go.mod

patch -p1 -d /app < "${ROOT_DIR}/patches/interval-floor.patch"
patch -p1 -d /app < "${ROOT_DIR}/patches/curtail-halfopen.patch"
patch -p1 -d /app < "${ROOT_DIR}/patches/market-exact.patch"
patch -p1 -d /app < "${ROOT_DIR}/patches/strike-max.patch"
patch -p1 -d /app < "${ROOT_DIR}/patches/holiday-net.patch"
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +

python3 /app/fixtures/build_fixtures.py
if [[ -d /opt/verifier-fixtures/ppareconctl ]]; then
  PPA_HIDDEN_ROOT=/opt/verifier-fixtures/ppareconctl python3 /app/fixtures/build_fixtures.py
fi

go build -mod=readonly -trimpath -ldflags="-s -w" -o /app/bin/ppareconctl ./cmd/ppareconctl
test -x /app/bin/ppareconctl
echo "renewable-ppa-settlement-engine oracle ready"
