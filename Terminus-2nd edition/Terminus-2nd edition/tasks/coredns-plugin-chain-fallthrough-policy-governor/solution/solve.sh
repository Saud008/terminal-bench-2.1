#!/usr/bin/env bash
set -euo pipefail

APP="/app"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

for patch in \
  chain-build.patch \
  chain-fallthrough.patch \
  chain-runner.patch \
  plugin-rewrite.patch \
  plugin-whoami.patch \
  plugin-cache.patch
do
  if [[ ! -f "${ROOT_DIR}/patches/${patch}" ]]; then
    echo "oracle missing patches/${patch}" >&2
    exit 1
  fi
done

cd "${APP}"
patch -p0 --forward -i "${ROOT_DIR}/patches/chain-build.patch"
patch -p0 --forward -i "${ROOT_DIR}/patches/chain-fallthrough.patch"
patch -p0 --forward -i "${ROOT_DIR}/patches/chain-runner.patch"
patch -p0 --forward -i "${ROOT_DIR}/patches/plugin-rewrite.patch"
patch -p0 --forward -i "${ROOT_DIR}/patches/plugin-whoami.patch"
patch -p0 --forward -i "${ROOT_DIR}/patches/plugin-cache.patch"

PATH="/usr/local/go/bin:/usr/local/bin:${PATH}"
go build -mod=readonly -o /usr/local/bin/dnsplugd ./cmd/dnsplugd
bash /app/scripts/reset-state.sh
