#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
cd /app
patch -p1 --forward --batch < "${ROOT_DIR}/patches/reader.go.patch"
patch -p1 --forward --batch < "${ROOT_DIR}/patches/election.go.patch"
patch -p1 --forward --batch < "${ROOT_DIR}/patches/commit.go.patch"
patch -p1 --forward --batch < "${ROOT_DIR}/patches/replay.go.patch"
patch -p1 --forward --batch < "${ROOT_DIR}/patches/truncate.go.patch"
patch -p1 --forward --batch < "${ROOT_DIR}/patches/config.go.patch"
patch -p1 --forward --batch < "${ROOT_DIR}/patches/seal.go.patch"
patch -p1 --forward --batch < "${ROOT_DIR}/patches/ledger.go.patch"
patch -p1 --forward --batch < "${ROOT_DIR}/patches/run.go.patch"

