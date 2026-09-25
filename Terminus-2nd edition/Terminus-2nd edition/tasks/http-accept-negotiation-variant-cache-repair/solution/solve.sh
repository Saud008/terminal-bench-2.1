#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TREE="${ROOT}/files"

cd /app

while IFS= read -r -d '' relpath; do
  src="${TREE}/${relpath}"
  dst="/app/${relpath}"
  mkdir -p "$(dirname "${dst}")"
  cp -f "${src}" "${dst}"
done < <(find "${TREE}" -type f -printf '%P\0')

go build -mod=readonly -o /usr/local/bin/variantgate ./cmd/variantgate
test -x /usr/local/bin/variantgate
