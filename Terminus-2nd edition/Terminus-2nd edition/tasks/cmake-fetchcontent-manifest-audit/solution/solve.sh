#!/usr/bin/env bash
if [ -f "${BASH_SOURCE[0]}" ]; then
  sed -i 's/\r$//' "${BASH_SOURCE[0]}" 2>/dev/null || true
fi
set -euo pipefail

export PATH="/app/bin:/usr/local/bin:${PATH}"
cd /app

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL=""
for candidate in "${SCRIPT_DIR}/files" "${SCRIPT_DIR}" "/solution/files" "/solution"; do
  if [ -f "${candidate}/lib/ingest.sh" ]; then
    SOL="${candidate}"
    break
  fi
done
[[ -n "${SOL}" ]] || { echo "solution lib/ingest.sh not found" >&2; exit 1; }

for f in \
  lib/normalize.sh \
  lib/ingest.sh \
  lib/export_tree.sh \
  lib/hash.sh \
  lib/fetch_closure.sh \
  lib/scan.sh \
  bin/cmake-audit
do
  cp -f "${SOL}/${f}" "/app/${f}"
  sed -i 's/\r$//' "/app/${f}"
done
chmod +x /app/bin/cmake-audit /app/lib/*.sh

bash /app/scripts/reset-state.sh
cmake-audit parse /app/project --output /app/data/cmake-tree.json --strict
cmake-audit hash-audit \
  --tree /app/data/cmake-tree.json \
  --vendor /app/vendor-cache \
  --pins /app/project/overlays/pinned.cmake \
  --output /app/data/hash-audit.json
cmake-audit scan \
  --tree /app/data/cmake-tree.json \
  --prefix /app/install \
  --output /app/output/install-manifest.json

echo "cmake-fetchcontent-manifest-audit oracle ready"
