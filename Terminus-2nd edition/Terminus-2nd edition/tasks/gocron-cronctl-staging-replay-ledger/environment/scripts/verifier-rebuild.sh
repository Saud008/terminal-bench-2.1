#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
cd /app

for sh in /app/scripts/*.sh; do
  sed -i 's/\r$//' "${sh}"
  chmod +x "${sh}"
done

while IFS= read -r -d '' src; do
  sed -i 's/\r$//' "${src}"
done < <(find /app/internal /app/cmd -name '*.go' -print0)

go build -mod=readonly -trimpath -ldflags="-s -w" -o /usr/local/bin/cronctl ./cmd/cronctl
