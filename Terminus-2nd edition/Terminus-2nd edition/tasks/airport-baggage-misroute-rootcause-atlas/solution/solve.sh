#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd /app
bash "${SCRIPT_DIR}/preflight.sh"

cd "${SCRIPT_DIR}"
patch -p0 -d /app < patches/ingress.patch
patch -p0 -d /app < patches/belt.patch
patch -p0 -d /app < patches/mct.patch
patch -p0 -d /app < patches/outage.patch
patch -p0 -d /app < patches/rank.patch
patch -p0 -d /app < patches/publish.patch
patch -p0 -d /app < patches/types_docs.patch

cd /app
/usr/local/cargo/bin/cargo build --release --locked
cp /app/target/release/bag-atlas /app/bin/bag-atlas
