#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILES="${ROOT_DIR}/files"
cd /app
for patch in "${FILES}"/*.patch; do
  patch -p1 --forward --batch < "${patch}"
done
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
