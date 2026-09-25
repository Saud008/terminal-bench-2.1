#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH="${ROOT_DIR}/patches/bond-accrual-oracle.patch"
cd /app
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
patch -p0 --forward --reject-file=- < "${PATCH}"
echo "bond accrual oracle patches applied"
