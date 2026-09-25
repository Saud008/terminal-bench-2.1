#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:${PATH:-}"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FILES="${ROOT}/solution/files"

while IFS= read -r -d '' src; do
  rel="${src#${FILES}/}"
  dest="/app/${rel}"
  mkdir -p "$(dirname "$dest")"
  cp "$src" "$dest"
done < <(find "$FILES" -type f -print0)

cd /app
go build -o /app/bin/lokictl ./cmd/lokictl
